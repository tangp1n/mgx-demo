# 前端事件显示问题修复

## 问题描述

用户反馈：前端总是在最后一条 assistant 消息的底部展示历史所有的事件。

## 根本原因

在 `Conversation.tsx` 的事件处理逻辑中：

1. **问题**：当处理 `thought`、`tool_call`、`tool_call_result` 事件时，代码总是将它们添加到**最后一个** assistant 消息
2. **影响**：如果用户发送了多条消息，每次都会创建新的 assistant 消息，但事件处理逻辑总是针对最后一个消息
3. **结果**：所有事件都累积在最后一个消息中，导致历史所有事件都显示在最后一条消息底部

## 修复方案

### 核心改进

1. **跟踪当前消息索引**：
   - 添加 `currentAssistantMessageIndex` 变量来跟踪当前正在处理的 assistant 消息的索引
   - 当收到 `text` 事件时，更新 `currentAssistantMessageIndex` 指向该消息

2. **事件关联到正确消息**：
   - 创建 `addEventToMessage` 辅助函数，将事件添加到指定索引的消息
   - 所有非 `text` 事件（`thought`、`tool_call`、`tool_call_result`）都添加到 `currentAssistantMessageIndex` 指向的消息
   - 如果 `currentAssistantMessageIndex` 为 null，使用 fallback 逻辑查找最后一个 assistant 消息

3. **防止事件累积**：
   - 确保每个事件只添加到当前正在处理的消息
   - 不会将事件添加到历史消息

### 代码变更

**文件**: `fe/src/components/Conversation/Conversation.tsx`

**主要变更**:
1. 添加 `currentAssistantMessageIndex` 变量跟踪当前消息索引
2. 创建 `addEventToMessage` 辅助函数
3. 在 `text` 事件处理中更新 `currentAssistantMessageIndex`
4. 在 `thought`、`tool_call`、`tool_call_result` 事件处理中使用 `currentAssistantMessageIndex`

**关键代码**:
```typescript
// Track the index of the current assistant message being processed
let currentAssistantMessageIndex: number | null = null;

// Helper function to add event to a specific message by index
const addEventToMessage = (messageIndex: number, event: SSEEvent) => {
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

// In text event handler:
// Set currentAssistantMessageIndex when creating/updating message
currentAssistantMessageIndex = prev.length; // or prev.length - 1

// In thought/tool_call/tool_call_result handlers:
if (currentAssistantMessageIndex !== null) {
  addEventToMessage(currentAssistantMessageIndex, event);
}
```

## 修复效果

修复后的代码应该能够：

1. **正确关联事件**：
   - 每个事件只添加到对应的 assistant 消息
   - 不会将事件添加到历史消息

2. **防止事件累积**：
   - 新消息的事件不会累积到旧消息中
   - 每个消息只显示自己的事件

3. **保持向后兼容**：
   - 如果 `currentAssistantMessageIndex` 为 null，使用 fallback 逻辑
   - 不会破坏现有功能

## 测试建议

1. **发送多条消息**：
   - 发送第一条消息，验证事件只显示在第一条 assistant 消息中
   - 发送第二条消息，验证事件只显示在第二条 assistant 消息中
   - 验证第一条消息的事件不会出现在第二条消息中

2. **刷新页面**：
   - 发送消息后刷新页面
   - 验证历史消息的事件仍然正确显示在各自的消息中

3. **检查事件显示**：
   - 验证 `thought`、`tool_call`、`tool_call_result` 事件都显示在正确的消息中
   - 验证不会出现事件重复或错误关联

## 相关文件

- `fe/src/components/Conversation/Conversation.tsx`: 前端消息和事件显示逻辑

