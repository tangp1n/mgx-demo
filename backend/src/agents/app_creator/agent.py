"""App creator agent using LangGraph."""
import asyncio
from typing import AsyncIterator, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .llm_config import get_llm
from .state import AgentState, ConversationStage
from ...utils.sse_formatter import SSEFormatter
from ...utils.logger import get_logger

logger = get_logger("app_creator.agent")


class AppCreatorAgent:
    """Agent for handling app creation conversations."""

    def __init__(self):
        """Initialize the app creator agent."""
        self.llm = get_llm()
        self.sse_formatter = SSEFormatter()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for app creation.

        Returns:
            Compiled state graph
        """
        workflow = StateGraph(AgentState)

        # Add only route_entry node - it handles all logic in one LLM call
        workflow.add_node("route_entry", self._route_entry_node)

        # Set entry point
        workflow.set_entry_point("route_entry")

        # route_entry always ends after processing (response already sent)
        workflow.add_edge("route_entry", END)

        # Compile with increased recursion limit
        return workflow.compile()

    async def _route_entry_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Smart entry routing node that uses LLM to analyze conversation history,
        determine current state, and generate appropriate response.

        Args:
            state: Current agent state

        Returns:
            Updated state with action decision and AI response
        """
        requirements_confirmed = state.get('requirements_confirmed', False)
        existing_requirements = state.get('requirements')
        existing_questions = state.get('clarifying_questions')

        logger.info(f"🚪 [route_entry] requirements_confirmed={requirements_confirmed}, has_requirements={bool(existing_requirements)}, questions={len(existing_questions) if existing_questions else 0}")

        # If already confirmed, end immediately
        if requirements_confirmed:
            logger.info("✅ [route_entry] Already confirmed -> END")
            return state

        # Build system prompt for LLM to analyze and decide
        system_prompt = """你是一个帮助用户通过对话创建应用的AI助手。

你的任务：分析当前对话历史，判断当前状态，并决定下一步行动，同时生成合适的回复。

**重要规则**：
- 你只负责需求收集和确认，不负责代码生成
- 绝对不要生成任何代码或代码示例
- 专注于理解用户的应用需求

**可能的行动类型**：

1. **clarify** - 需要澄清问题
   - 当需求存在根本性模糊（会完全阻碍实施）时
   - 信息不全，需要澄清
   - 最多只问1个最关键的问题
   - 生成澄清问题的回复

2. **extract** - 提取需求并确认
   - 当对话中已经收集到足够的信息来理解应用需求时
   - 信息已全，当场提取需求
   - 从对话中提取并结构化需求
   - 生成回复，向用户确认是否要开始创建应用
   - 这是提取和确认的合并操作

3. **start_gen** - 开始代码生成
   - 当需求已经提取，用户明确确认要开始时使用
   - 用户已经确认了要开始，触发后续的代码生成流程
   - 用户回复包含确认关键词（如"确认"、"是的"、"可以"、"开始"、"好的"、"ok"等）时使用
   - 生成确认消息，表示即将开始构建

4. **continue** - 继续对话
   - 当需要更多信息来理解用户需求时
   - 继续与用户对话，收集更多信息

**判断逻辑**：
- 如果已有需求且用户消息包含确认关键词（确认、是的、可以、开始、好的、ok、okay、yes等），使用 **start_gen**
- 如果已有需求但用户未确认，使用 **extract** 来提取并询问确认
- 如果信息不全，使用 **clarify** 或 **continue**

**输出格式（必须是有效的JSON）**：
{{
  "action": "clarify" | "extract" | "start_gen" | "continue",
  "response": "AI的回复文本（中文）",
  "requirements": "如果action是extract或start_gen，这里是提取的需求文本（中文），否则为null",
  "clarifying_questions": ["如果action是clarify，这里是问题列表（最多1个），否则为[]"]
}}

**当前状态信息**：
- 已有需求: {has_requirements}
- 已有澄清问题: {has_questions}

**重要**：请严格按照JSON格式输出，不要添加任何额外的文本或说明。""".format(
            has_requirements="是" if existing_requirements else "否",
            has_questions="是" if existing_questions else "否"
        )

        # Build messages for LLM
        messages = [SystemMessage(content=system_prompt)] + state["messages"]

        # Get LLM response
        logger.info("🤖 [route_entry] Calling LLM to analyze conversation and decide action...")
        response = await asyncio.to_thread(self.llm.invoke, messages)
        logger.info(f"✅ [route_entry] LLM response received ({len(response.content)} chars)")

        # Parse LLM response (expecting JSON)
        import json
        import re

        action = "continue"
        ai_response = ""
        extracted_requirements = None
        clarifying_questions = None

        try:
            # Try to extract JSON from response
            content = response.content.strip()

            # Remove markdown code blocks if present
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()

            # Try to find JSON object
            # First, try parsing the entire content
            try:
                result = json.loads(content)
                action = result.get("action", "continue")
                ai_response = result.get("response", "")
                extracted_requirements = result.get("requirements")
                clarifying_questions = result.get("clarifying_questions", [])
            except json.JSONDecodeError:
                # If that fails, try to extract JSON block
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    action = result.get("action", "continue")
                    ai_response = result.get("response", "")
                    extracted_requirements = result.get("requirements")
                    clarifying_questions = result.get("clarifying_questions", [])
                else:
                    # If no JSON found, treat entire response as text and default to continue
                    ai_response = content
                    logger.warning("⚠️  [route_entry] No JSON found in LLM response, using as text response")

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"❌ [route_entry] Failed to parse LLM response: {e}, content: {response.content[:200]}")
            # Fallback: use response as text
            ai_response = response.content
            action = "continue"

        logger.info(f"🎯 [route_entry] LLM decided action: {action}")

        # Update state based on action
        updated_state = {**state}
        new_messages = state["messages"].copy()

        if action == "clarify":
            # Need to clarify - 信息不全，需要澄清
            if ai_response:
                new_messages.append(AIMessage(content=ai_response))
            updated_state["clarifying_questions"] = clarifying_questions or []
            updated_state["current_stage"] = ConversationStage.CLARIFYING
            logger.info(f"❓ [route_entry] Action: clarify, questions: {clarifying_questions}")

        elif action == "extract":
            # Extract requirements - 信息已全，当场提取，并向用户确认是否要开始
            if extracted_requirements:
                updated_state["requirements"] = extracted_requirements
                logger.info(f"📋 [route_entry] Extracted requirements ({len(extracted_requirements)} chars)")
            if ai_response:
                new_messages.append(AIMessage(content=ai_response))
            # After extraction, ask user to confirm if they want to start
            updated_state["current_stage"] = ConversationStage.CONFIRMING
            updated_state["clarifying_questions"] = []
            logger.info("📋 [route_entry] Extracted requirements, asking for confirmation")

        elif action == "start_gen":
            # Start generation - 用户已经确认了要开始，触发后续的代码生成流程
            if extracted_requirements:
                updated_state["requirements"] = extracted_requirements
                logger.info(f"📋 [route_entry] Updated requirements ({len(extracted_requirements)} chars)")
            if ai_response:
                new_messages.append(AIMessage(content=ai_response))
            # User confirmed, set confirmed and trigger code generation
            updated_state["requirements_confirmed"] = True
            updated_state["current_stage"] = ConversationStage.CONFIRMED
            updated_state["clarifying_questions"] = []
            logger.info("✅ [route_entry] User confirmed, starting code generation")

        else:  # continue
            # Continue conversation - 需要更多信息来理解用户需求
            if ai_response:
                new_messages.append(AIMessage(content=ai_response))
            updated_state["current_stage"] = ConversationStage.GATHERING
            logger.info("💬 [route_entry] Continue conversation")

        updated_state["messages"] = new_messages
        return updated_state

    async def stream_conversation(
        self,
        application_id: str,
        user_id: str,
        user_message: str,
        existing_messages: list = None,
        app_service=None
    ) -> AsyncIterator[str]:
        """
        Stream conversation events as SSE.

        Args:
            application_id: Application ID
            user_id: User ID
            user_message: User's message
            existing_messages: Existing conversation messages
            app_service: Application service for updating database (optional)

        Yields:
            SSE formatted events
        """
        try:
            # Initialize state
            messages = existing_messages or []
            messages.append(HumanMessage(content=user_message))

            # Try to restore state from database if app_service is provided
            requirements = None
            requirements_confirmed = False
            current_stage = ConversationStage.GATHERING
            clarifying_questions = None

            if app_service:
                try:
                    # Yield control before await to prevent blocking in nested async generators
                    await asyncio.sleep(0)
                    app = await app_service.get(application_id=application_id, user_id=user_id)
                    if app:
                        requirements = app.requirements
                        requirements_confirmed = app.requirements_confirmed
                        # Determine stage based on state
                        if requirements_confirmed:
                            current_stage = ConversationStage.CONFIRMED
                        elif requirements:
                            # Check if we've asked clarifying questions by looking at messages
                            # For now, assume no questions if requirements exist
                            clarifying_questions = []
                            current_stage = ConversationStage.CLARIFYING
                        else:
                            current_stage = ConversationStage.GATHERING
                        logger.info(f"📦 [stream] Restored state: requirements={bool(requirements)}, confirmed={requirements_confirmed}, stage={current_stage}")
                except Exception as e:
                    logger.warning(f"⚠️  [stream] Failed to restore state from database: {e}")

            state = AgentState(
                messages=messages,
                application_id=application_id,
                user_id=user_id,
                requirements=requirements,
                requirements_confirmed=requirements_confirmed,
                clarifying_questions=clarifying_questions,
                current_stage=current_stage,
                error=None
            )

            # Yield thought event
            yield self.sse_formatter.format_thought("Processing your message...")

            # Track final state to get the last response
            final_state = None
            initial_message_count = len(state.get("messages", []))

            # Run the graph with config to increase recursion limit
            config = {"recursion_limit": 50}  # Increase from default 25

            # Run the graph
            logger.info(f"🚀 [stream] Starting graph execution (stage: {state.get('current_stage')}, messages: {len(state.get('messages', []))})")

            last_sent_message_count = initial_message_count  # Track how many messages we've already sent
            sent_message_hashes = set()  # Track sent message content hashes to avoid duplicates

            async for event in self.graph.astream(state, config=config):
                # Yield control to event loop to prevent blocking in nested async generators
                await asyncio.sleep(0)

                # Extract node name and state
                node_name = list(event.keys())[0]
                node_state = event[node_name]

                logger.info(f"🔄 [graph] Executed node: {node_name}")

                # Update final state (keep the latest state)
                final_state = node_state

                # Yield thought events for processing
                if node_name == "route_entry":
                    logger.info("🚪 [stream] Entry routing completed")

                    # Send AI response if generated
                    current_messages = node_state.get("messages", [])
                    if current_messages and len(current_messages) > last_sent_message_count:
                        new_messages = current_messages[last_sent_message_count:]
                        for message in new_messages:
                            if isinstance(message, AIMessage):
                                msg_hash = hash(message.content)
                                if msg_hash not in sent_message_hashes:
                                    yield self.sse_formatter.format_text(message.content)
                                    sent_message_hashes.add(msg_hash)
                        last_sent_message_count = len(current_messages)

                    # Check if requirements were extracted
                    if node_state.get("requirements") and not state.get("requirements"):
                        requirements = node_state.get("requirements")
                        logger.info(f"📋 [route_entry] Requirements extracted ({len(requirements)} chars)")

                        # Update database
                        if app_service:
                            try:
                                from ...models.application import ApplicationUpdate
                                # Yield control before await to prevent blocking
                                await asyncio.sleep(0)
                                await app_service.update(
                                    application_id=application_id,
                                    user_id=user_id,
                                    data=ApplicationUpdate(requirements=requirements)
                                )
                                logger.info(f"💾 [route_entry] Updated requirements in database")

                                # Write requirements to container immediately when extracted (no need to wait for confirmation)
                                try:
                                    from ...services.container.container_lifecycle import ContainerLifecycleService

                                    # Get database connection from app_service
                                    db = app_service.db
                                    container_lifecycle = ContainerLifecycleService(db)
                                    # Yield control before await to prevent blocking
                                    await asyncio.sleep(0)
                                    await container_lifecycle.write_task_file(
                                        application_id=application_id,
                                        requirements=requirements
                                    )
                                    logger.info(f"📝 [route_entry] Wrote requirements to container for application {application_id}")
                                except Exception as e:
                                    logger.error(f"❌ [route_entry] Failed to write requirements to container: {e}", exc_info=True)
                            except Exception as e:
                                logger.error(f"❌ [route_entry] Failed to update requirements: {e}", exc_info=True)

                    # Check if requirements were confirmed
                    if node_state.get('requirements_confirmed', False):
                        logger.info("✅ [stream] Requirements confirmed in route_entry")

                        # Update database if app_service is provided
                        if app_service:
                            requirements = node_state.get("requirements")
                            if requirements:
                                try:
                                    # Yield control before await to prevent blocking
                                    await asyncio.sleep(0)
                                    await app_service.confirm_requirements(
                                        application_id=application_id,
                                        user_id=user_id
                                    )
                                    from ...models.application import ApplicationUpdate
                                    # Yield control before await to prevent blocking
                                    await asyncio.sleep(0)
                                    await app_service.update(
                                        application_id=application_id,
                                        user_id=user_id,
                                        data=ApplicationUpdate(requirements=requirements)
                                    )
                                    logger.info(f"💾 [route_entry] Updated application {application_id} in database")

                                    # Requirements should already be written to container when extracted
                                    # But update it again in case requirements were updated during confirmation
                                    try:
                                        from ...services.container.container_lifecycle import ContainerLifecycleService

                                        # Get database connection from app_service
                                        db = app_service.db
                                        container_lifecycle = ContainerLifecycleService(db)
                                        # Yield control before await to prevent blocking
                                        await asyncio.sleep(0)
                                        await container_lifecycle.write_task_file(
                                            application_id=application_id,
                                            requirements=requirements
                                        )
                                        logger.info(f"📝 [route_entry] Updated requirements in container for application {application_id}")
                                    except Exception as e:
                                        logger.error(f"❌ [route_entry] Failed to update requirements in container: {e}", exc_info=True)
                                except Exception as e:
                                    logger.error(f"❌ [route_entry] Failed to update application: {e}", exc_info=True)

                        # Emit requirements_confirmed event
                        # This event will be detected by conversations.py to trigger code generation
                        yield self.sse_formatter.format_event({
                            "type": "requirements_confirmed",
                            "data": {
                                "requirements": node_state.get("requirements", ""),
                                "message": "Requirements confirmed, starting code generation..."
                            }
                        })


            # Send any remaining AI messages from the final state (should be none if confirmation_node ran)
            # This is a safety net for edge cases
            if final_state:
                final_messages = final_state.get("messages", [])
                if final_messages and len(final_messages) > last_sent_message_count:
                    logger.warning(f"⚠️  [stream] Fallback: {len(final_messages) - last_sent_message_count} unsent messages")
                    new_messages = final_messages[last_sent_message_count:]
                    for message in new_messages:
                        if isinstance(message, AIMessage):
                            # Use content hash to avoid duplicates
                            msg_hash = hash(message.content)
                            if msg_hash not in sent_message_hashes:
                                yield self.sse_formatter.format_text(message.content)
                                sent_message_hashes.add(msg_hash)

            # Yield done event
            yield self.sse_formatter.format_done()

        except Exception as e:
            yield self.sse_formatter.format_error(str(e))
            yield self.sse_formatter.format_done()
