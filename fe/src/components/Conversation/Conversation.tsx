import React, { useState, useEffect, useRef } from "react";
import { Application } from "../../types/api";
import { conversationAPI, applicationAPI } from "../../services/api";
import { SSEClient, SSEEvent } from "../../services/sse";

interface ConversationProps {
  application: Application;
  onRequirementsConfirmed?: () => void;
  onApplicationUpdate?: (application: Application) => void;
}

const Conversation: React.FC<ConversationProps> = ({
  application,
  onRequirementsConfirmed,
  onApplicationUpdate,
}) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sseClient] = useState(() => new SSEClient());
  const [isGenerating, setIsGenerating] = useState(false);
  const currentAssistantMessageIndexRef = useRef<number | null>(null);

  const applicationId = application._id || application.id || "";

  // Check if code generation is in progress
  const isCodeGenerating = application.status === "generating" || application.status === "deploying";

  // Check if requirements are confirmed and ready for code generation
  const canStartGeneration = application.status === "requirements_confirmed" && !isCodeGenerating;

  const startCodeGeneration = async () => {
    if (!canStartGeneration || isGenerating) {
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      // Add system message indicating generation is starting
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "🚀 开始生成代码... 请稍候，我会在容器中创建您的应用程序。",
          timestamp: new Date().toISOString(),
          events: [],
        },
      ]);

      // Connect to code generation stream
      const streamUrl = applicationAPI.getGenerateStreamUrl(applicationId);

      // Clear previous connection
      sseClient.close();

      // Track the current assistant message index for code generation events
      let currentMessageIndex = messages.length; // This will be the index of the generation message

      const eventHandler = (event: SSEEvent) => {
        if (event.type === "text") {
          // Update the last assistant message with new text content
          setMessages((prev) => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === "assistant") {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  content: event.data.content,
                },
              ];
            }
            return prev;
          });
        } else if (event.type === "thought" || event.type === "tool_call" || event.type === "tool_call_result") {
          // Add events to the current generation message
          setMessages((prev) => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === "assistant") {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastMessage,
                  events: [...(lastMessage.events || []), event],
                },
              ];
            }
            return prev;
          });
        } else if (event.type === "error") {
          setError(event.data.message || "代码生成失败");
          setIsGenerating(false);
        } else if (event.type === "done" || event.data?.type === "done") {
          setIsGenerating(false);
        }
      };

      sseClient.onEvent(eventHandler);
      sseClient.connect(streamUrl);

    } catch (err: any) {
      console.error("Failed to start code generation:", err);
      setError("启动代码生成失败");
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    // Load conversation history when component mounts
    const loadConversation = async () => {
      try {
        const conversation = await conversationAPI.get(applicationId);
        if (conversation.messages && conversation.messages.length > 0) {
          // Convert API messages to component message format
          const formattedMessages = conversation.messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            events: msg.events || [],
          }));
          setMessages(formattedMessages);
          // Reset the current assistant message index when loading history
          // Historical messages are already completed, so no message should be "current"
          currentAssistantMessageIndexRef.current = null;
        }
      } catch (err: any) {
        // Log error but don't show it to user if conversation doesn't exist yet
        if (err.response?.status !== 404) {
          console.error("Failed to load conversation:", err);
        }
      }
    };

    loadConversation();

    // Cleanup SSE connection on unmount
    return () => {
      sseClient.close();
      // Reset index on unmount
      currentAssistantMessageIndexRef.current = null;
    };
  }, [applicationId, sseClient]);

  // Poll application status to detect when it changes to requirements_confirmed
  // This is more reliable than relying on SSE events
  useEffect(() => {
    // Only poll when application is in draft state (waiting for confirmation)
    if (application.status !== "draft") {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const updatedApp = await applicationAPI.get(applicationId);
        // If status changed, notify parent to update
        if (updatedApp.status !== application.status) {
          if (onApplicationUpdate) {
            onApplicationUpdate(updatedApp);
          }
        }
      } catch (err) {
        console.error("Failed to poll application status:", err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application.status, applicationId]); // onApplicationUpdate is stable from props

  const handleSendMessage = async (message: string) => {
    setError(null);
    setLoading(true);

    // Reset the current assistant message index before starting a new message
    currentAssistantMessageIndexRef.current = null;

    // Add user message and create assistant message placeholder immediately
    // Store the index of the new assistant message in a ref
    setMessages((prev) => {
      const userMessage = {
        role: "user" as const,
        content: message,
        timestamp: new Date().toISOString(),
      };
      // Create an empty assistant message placeholder immediately
      // This ensures all events (including thought events) are added to the correct message
      const assistantMessage = {
        role: "assistant" as const,
        content: "",
        timestamp: new Date().toISOString(),
        events: [] as SSEEvent[],
      };
      // Store the index of the new assistant message (after adding both messages)
      const newAssistantIndex = prev.length + 1;
      currentAssistantMessageIndexRef.current = newAssistantIndex;
      return [...prev, userMessage, assistantMessage];
    });

    try {
      // Send message to backend
      await conversationAPI.sendMessage(applicationId, message);

      // Connect to SSE stream
      const streamUrl = conversationAPI.getStreamUrl(applicationId);

      // Clear previous connection if any
      sseClient.close();

      // Track text event count to create separate messages
      let textEventCount = 0;
      // Track sent message content to avoid duplicates
      const sentMessageHashes = new Set<string>();

      // Helper function to add event to a specific message by index
      const addEventToMessage = (
        messageIndex: number,
        event: SSEEvent
      ) => {
        setMessages((prev) => {
          if (messageIndex < 0 || messageIndex >= prev.length) {
            return prev;
          }
          const targetMessage = prev[messageIndex];
          if (targetMessage && targetMessage.role === "assistant") {
            return [
              ...prev.slice(0, messageIndex),
              {
                ...targetMessage,
                events: [...(targetMessage.events || []), event],
              },
              ...prev.slice(messageIndex + 1),
            ];
          }
          return prev;
        });
      };

      // Define event handler
      const eventHandler = (event: SSEEvent) => {
        // Get the current index from ref
        let currentIndex = currentAssistantMessageIndexRef.current;

        // If no index is set, try to find the last assistant message as fallback
        if (currentIndex === null) {
          // Use a functional update to access current state and find the index
          setMessages((prev) => {
            // Find the last assistant message
            for (let i = prev.length - 1; i >= 0; i--) {
              if (prev[i].role === "assistant") {
                currentAssistantMessageIndexRef.current = i;
                break;
              }
            }
            // Return unchanged since we're just reading
            return prev;
          });

          // Re-read the ref after the update
          currentIndex = currentAssistantMessageIndexRef.current;

          // If still no index found, skip this event
          if (currentIndex === null) {
            console.warn("No current assistant message index set, skipping event");
            return;
          }
        }

        if (event.type === "text") {
          const content = event.data.content;
          if (!content) return;

          // Use content hash to avoid duplicates
          const contentHash = content; // Simple hash using content itself

          // Check if we've already seen this exact content
          if (sentMessageHashes.has(contentHash)) {
            console.log("Skipping duplicate text event:", content.substring(0, 50));
            return;
          }

          sentMessageHashes.add(contentHash);
          textEventCount++;

          // Update the current assistant message with text content
          setMessages((prev) => {
            // Re-verify the index is still valid
            if (currentIndex === null || currentIndex < 0 || currentIndex >= prev.length) {
              return prev;
            }
            const targetMessage = prev[currentIndex];
            if (targetMessage && targetMessage.role === "assistant") {
              return [
                ...prev.slice(0, currentIndex),
                {
                  ...targetMessage,
                  content: content,
                  timestamp: event.timestamp || targetMessage.timestamp,
                },
                ...prev.slice(currentIndex + 1),
              ];
            }
            return prev;
          });
        } else if (event.type === "thought") {
          // Add thought events to the current assistant message being processed
          // Only add if we have a valid index
          if (currentIndex !== null) {
            addEventToMessage(currentIndex, event);
          }
        } else if (event.type === "tool_call") {
          // Add tool call events to the current assistant message being processed
          if (currentIndex !== null) {
            addEventToMessage(currentIndex, event);
          }
        } else if (event.type === "tool_call_result") {
          // Add tool call result events to the current assistant message being processed
          if (currentIndex !== null) {
            addEventToMessage(currentIndex, event);
          }
        } else if (event.type === "requirements_confirmed") {
          // When requirements are confirmed, refresh application status
          // The polling mechanism will also detect this, but we can refresh immediately here
          applicationAPI.get(applicationId)
            .then((updatedApp) => {
              if (onApplicationUpdate) {
                onApplicationUpdate(updatedApp);
              }
              if (onRequirementsConfirmed) {
                onRequirementsConfirmed();
              }
            })
            .catch((err) => {
              console.error("Failed to refresh application after requirements confirmed:", err);
            });
        } else if (event.type === "error") {
          setError(event.data.message);
        }
      };

      sseClient.onEvent(eventHandler);

      sseClient.connect(streamUrl);
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to send message");
      // Reset the index on error
      currentAssistantMessageIndexRef.current = null;
    } finally {
      setLoading(false);
    }
  };

  const renderEvent = (event: SSEEvent, idx: number) => {
    switch (event.type) {
      case "thought":
        return (
          <div key={idx} className="event event-thought">
            <div className="event-icon">💭</div>
            <div className="event-content">
              <em>{event.data.content}</em>
            </div>
          </div>
        );

      case "tool_call":
        const toolName = event.data.tool || event.data.tool_name || "Unknown Tool";
        const toolInput = event.data.input || event.data.arguments || {};

        return (
          <div key={idx} className="event event-tool-call">
            <div className="event-icon">🔧</div>
            <div className="event-content">
              <div className="event-title">
                <strong>Tool:</strong> {toolName}
              </div>
              {Object.keys(toolInput).length > 0 && (
                <div className="event-details">
                  {Object.entries(toolInput).map(([key, value]) => (
                    <div key={key} className="event-detail-item">
                      <span className="detail-key">{key}:</span>
                      <span className="detail-value">
                        {typeof value === "string" ? value : JSON.stringify(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case "tool_call_result":
        const success = event.data.success !== false;
        const result = event.data.result || event.data;

        return (
          <div key={idx} className={`event event-tool-result ${success ? 'success' : 'error'}`}>
            <div className="event-icon">{success ? "✅" : "❌"}</div>
            <div className="event-content">
              <div className="event-title">
                <strong>Result:</strong> {success ? "Success" : "Failed"}
              </div>
              {result.message && (
                <div className="event-message">{result.message}</div>
              )}
              {result.error && (
                <div className="event-error">{result.error}</div>
              )}
            </div>
          </div>
        );

      case "text":
        // Text events are already shown in the message content
        return null;

      case "error":
        return (
          <div key={idx} className="event event-error">
            <div className="event-icon">⚠️</div>
            <div className="event-content">
              <strong>Error:</strong> {event.data.message || event.data.error}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Find the index of the latest assistant message (computed once before rendering)
  const findLatestAssistantMessageIndex = () => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant") {
        return i;
      }
    }
    return -1;
  };

  const latestAssistantMessageIndex = findLatestAssistantMessageIndex();

  const renderMessage = (message: any, index: number) => {
    const hasContent = message.content && message.content.trim().length > 0;
    const hasEvents = message.events && message.events.length > 0;

    // Check if this is the latest assistant message
    const isLatestAssistantMessage =
      message.role === "assistant" &&
      index === latestAssistantMessageIndex;

    // Only show "思考中..." for the latest assistant message that has no content but has events
    // This indicates it's currently being processed
    const showProcessingIndicator =
      !hasContent &&
      hasEvents &&
      isLatestAssistantMessage;

    // Only show events for the latest unfinished assistant message (no content means still processing)
    const shouldShowEvents =
      hasEvents &&
      isLatestAssistantMessage &&
      !hasContent;

    return (
      <div key={index} className={`message message-${message.role}`}>
        <div className="message-content">
          <strong>{message.role === "user" ? "You" : "Assistant"}:</strong>
          {hasContent ? (
            <p>{message.content}</p>
          ) : showProcessingIndicator ? (
            <p className="message-placeholder">思考中...</p>
          ) : null}
        </div>

        {/* Only show process events for the latest unfinished assistant message */}
        {shouldShowEvents && (
          <div className="message-events">
            {message.events.map((event: SSEEvent, idx: number) => renderEvent(event, idx))}
          </div>
        )}

        <div className="message-timestamp">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    );
  };

  return (
    <div className="conversation">
      <div className="conversation-header">
        <h3>Conversation</h3>
        <span className="application-status">{application.status}</span>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="conversation-messages">
        {messages.length === 0 ? (
          <div className="conversation-empty">
            <p>Start a conversation to refine your application requirements.</p>
          </div>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
      </div>

      {/* Show code generation button when requirements are confirmed */}
      {canStartGeneration && (
        <div className="conversation-actions" style={{ padding: "1rem", borderTop: "1px solid #eee" }}>
          <button
            onClick={startCodeGeneration}
            disabled={isGenerating}
            style={{
              width: "100%",
              padding: "0.75rem",
              fontSize: "1rem",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: isGenerating ? "not-allowed" : "pointer",
              opacity: isGenerating ? 0.6 : 1,
            }}
          >
            {isGenerating ? "正在生成代码..." : "🚀 开始生成代码"}
          </button>
        </div>
      )}

      <div className="conversation-input">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const input = e.currentTarget.elements.namedItem(
              "message"
            ) as HTMLInputElement;
            if (input.value.trim()) {
              handleSendMessage(input.value);
              input.value = "";
            }
          }}
        >
          <input
            type="text"
            name="message"
            placeholder="Type your message..."
            disabled={loading || isCodeGenerating}
          />
          <button type="submit" disabled={loading || isCodeGenerating}>
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Conversation;
