import { API_CONFIG, ERROR_MESSAGES } from './constants';

const API_URL = API_CONFIG.BASE_URL;

export interface ChatRequest {
    message: string;
    session_id?: string;
    conversation_history?: Array<{
        role: string;
        content: string;
        timestamp: string;
    }>;
}

export interface ChatResponse {
    message: string;
    intent: string;
    products: Array<{
        id: number;
        name: string;
        brand: string;
        price: number;
        key_specs: { [key: string]: string };
        highlights: string[];
        rating?: number;
    }>;
    confidence: number;
    is_safe: boolean;
    safety_message?: string;
    session_id: string;
    suggestions: string[];
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || ERROR_MESSAGES.API_FAILED);
        }

        const data = await response.json();
        return data;
    } catch (error: any) {
        console.error('API Error:', error);
        throw new Error(error.message || ERROR_MESSAGES.NETWORK);
    }
}
