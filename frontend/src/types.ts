export interface ChatMetadata {
  client_phone?: string;
  client_name?: string;
  client_details?: string;
  start_timestamp?: string;
  [key: string]: unknown;
}

export interface ChatSummary {
  id: string;
  metadata: ChatMetadata;
}

export interface Chat {
  metadata: ChatMetadata;
  generated: string[];
  past: string[];
  messages: any[];
}

export interface TelegramMessage {
  sender: string;
  text: string;
  timestamp: number;
}
