/**
 * SSE client for streaming agent events.
 */

export interface SSEEvent {
  type: "thought" | "tool_call" | "tool_call_result" | "text" | "error" | "requirements_confirmed" | "done";
  data: any;
  timestamp: string;
}

export type SSECallback = (event: SSEEvent) => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private callbacks: SSECallback[] = [];

  /**
   * Connect to SSE stream.
   *
   * @param url - SSE endpoint URL
   * @param token - Authentication token
   */
  connect(url: string, token?: string): void {
    // Add token to URL if provided
    const fullUrl = token ? `${url}?token=${token}` : url;

    this.eventSource = new EventSource(fullUrl);

    this.eventSource.onmessage = (event) => {
      const data = event.data.trim();

      if (data === "[DONE]") {
        this.close();
        return;
      }

      try {
        const parsedEvent: SSEEvent = JSON.parse(data);
        this.notifyCallbacks(parsedEvent);
      } catch (error) {
        console.error("Failed to parse SSE event:", error, "Data:", data);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      // Don't close on error - EventSource will automatically reconnect
      // Only close if readyState is CLOSED
      if (this.eventSource && this.eventSource.readyState === EventSource.CLOSED) {
        this.close();
      }
    };
  }

  /**
   * Add callback for SSE events.
   *
   * @param callback - Callback function
   */
  onEvent(callback: SSECallback): void {
    this.callbacks.push(callback);
  }

  /**
   * Remove callback.
   *
   * @param callback - Callback to remove
   */
  offEvent(callback: SSECallback): void {
    this.callbacks = this.callbacks.filter((cb) => cb !== callback);
  }

  /**
   * Close SSE connection.
   */
  close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  /**
   * Check if connected.
   */
  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }

  /**
   * Notify all callbacks of an event.
   *
   * @param event - SSE event
   */
  private notifyCallbacks(event: SSEEvent): void {
    this.callbacks.forEach((callback) => callback(event));
  }
}

/**
 * Create a new SSE client instance.
 */
export function createSSEClient(): SSEClient {
  return new SSEClient();
}
