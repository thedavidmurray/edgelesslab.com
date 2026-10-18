/**
 * Agent Bus Client -- TypeScript client for the Agent Bus Hub
 *
 * Usage:
 *   const client = new AgentBusClient("worker-content", "http://127.0.0.1:9800");
 *   await client.register();
 *   await client.send("dispatch", { task_id: "rss-001", status: "done" });
 *   const messages = await client.poll();
 */

export interface Message {
  id: string;
  mailbox: string;
  from_sender: string;
  content: string;
  type: "request" | "response" | "broadcast" | "heartbeat";
  status: string;
  created_at: string;
}

export class AgentBusClient {
  constructor(
    public readonly name: string,
    private hubUrl: string = process.env.AGENT_BUS_HUB ?? "http://127.0.0.1:9800",
  ) {}

  private async request(path: string, method: string, body?: unknown): Promise<unknown> {
    const res = await fetch(`${this.hubUrl}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(`Hub error: ${JSON.stringify(err)}`);
    }
    return res.json();
  }

  /** Register this client with the hub. Call once on startup. */
  async register(): Promise<void> {
    await this.request("/register", "POST", { name: this.name });
  }

  /** Send a message to a named recipient. */
  async send(
    to: string,
    content: string | Record<string, unknown>,
    type: string = "request",
    ttl?: number,
  ): Promise<void> {
    const payload = typeof content === "string" ? content : JSON.stringify(content);
    await this.request("/send", "POST", {
      from: this.name,
      to,
      content: payload,
      type,
      ...(ttl ? { ttl } : {}),
    });
  }

  /** Broadcast a message to all connected sessions. */
  async broadcast(
    content: string | Record<string, unknown>,
    type: string = "broadcast",
  ): Promise<{ recipients: number }> {
    const payload = typeof content === "string" ? content : JSON.stringify(content);
    return this.request("/broadcast", "POST", {
      from: this.name,
      content: payload,
      type,
    }) as Promise<{ recipients: number }>;
  }

  /** Poll for pending messages. Returns leased messages that must be acked. */
  async poll(): Promise<Message[]> {
    return this.request(`/poll/${this.name}`, "GET") as Promise<Message[]>;
  }

  /** Acknowledge a message (mark as processed). */
  async ack(messageId: string): Promise<void> {
    await this.request("/ack", "POST", { id: messageId });
  }

  /** List all connected sessions. */
  async sessions(): Promise<{ name: string; connected_at: string; last_seen: string }[]> {
    return this.request("/sessions", "GET") as Promise<{ name: string; connected_at: string; last_seen: string }[]>;
  }

  /** Health check. */
  async health(): Promise<{ status: string; pending_messages: number }> {
    return this.request("/health", "GET") as Promise<{ status: string; pending_messages: number }>;
  }

  /**
   * Wait for a response matching a task ID.
   * Polls every 2 seconds until a matching response arrives or timeout.
   */
  async waitForResponse(taskId: string, timeoutMs: number = 300_000): Promise<Record<string, unknown>> {
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
      const messages = await this.poll();

      for (const msg of messages) {
        try {
          const parsed = JSON.parse(msg.content);
          if (parsed.task_id === taskId) {
            await this.ack(msg.id);
            return parsed;
          }
        } catch {
          // Not JSON, ack and skip
          await this.ack(msg.id);
        }
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error(`Timeout waiting for response to task ${taskId}`);
  }
}
