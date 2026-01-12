/**
 * Application Constants
 * All hardcoded values, strings, and configuration constants
 */

// API Configuration
export const API_CONFIG = {
    BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3,
} as const;

// Application Metadata
export const APP_METADATA = {
    NAME: 'ShopAI',
    FULL_NAME: 'Shopping Agent',
    VERSION: 'v2.0',
    TAGLINE: 'AI Phone Expert',
} as const;

// UI Text Constants
export const UI_TEXT = {
    WELCOME: {
        TITLE: 'The Future of Shopping is Here',
        SUBTITLE: "I'm your personal AI expert. Whether you need a gaming beast, a camera pro, or a budget king, I'll find it instantly.",
        GAMING_LABEL: 'gaming beast',
        CAMERA_LABEL: 'camera pro',
        BUDGET_LABEL: 'budget king',
    },
    FEATURES: [
        {
            title: 'Instant Compare',
            description: 'Compare specs side-by-side in milliseconds.',
        },
        {
            title: 'Real-time Prices',
            description: 'Always get the latest pricing and deals.',
        },
        {
            title: 'Unbiased AI',
            description: 'Recommendations based on specs, not ads.',
        },
    ],
    SUGGESTIONS: {
        TITLE: 'Try asking about',
        PROMPTS: [
            'Best camera phone under ₹40,000',
            'Gaming phones with 120Hz display',
            'iPhone 15 vs Samsung S24',
            '5G phones with best battery life',
        ],
    },
    CHAT: {
        LOADING: 'Analyzing products...',
        ERROR_DEFAULT: 'Sorry, I encountered an error. Please try again.',
        PRODUCTS_FOUND: 'Products Found',
        INPUT_PLACEHOLDER: 'Ask for recommendations, specs, or comparisons...',
        DISCLAIMER: 'AI can make mistakes. Please check product details.',
    },
    SIDEBAR: {
        NEW_CHAT: 'New Chat',
        RECENT: 'Recent',
        SETTINGS: 'Settings',
        USER_NAME: 'Guest User',
        USER_PLAN: 'Free Plan',
        HISTORY_ITEMS: [
            'Best gaming phones...',
            'iPhone vs Samsung...',
            'Budget 5G options...',
        ],
    },
} as const;

// Styling Constants
export const COLORS = {
    BACKGROUND: '#09090b',
    CARD_BG: '#18181b',
    BORDER: '#27272a',
    BORDER_HOVER: '#3f3f46',
    PRIMARY: '#3b82f6',
    PRIMARY_DARK: '#2563eb',
} as const;

// Animation Delays
export const ANIMATION = {
    BOUNCE_DELAYS: ['0ms', '150ms', '300ms'],
    TRANSITION_DURATION: 300,
} as const;

// Conversation Settings
export const CONVERSATION = {
    MAX_HISTORY: 5,
    AUTO_SCROLL_BEHAVIOR: 'smooth' as ScrollBehavior,
} as const;

// Error Messages
export const ERROR_MESSAGES = {
    NETWORK: 'Network error. Please check your connection.',
    API_FAILED: 'Failed to send message',
    GENERIC: 'Something went wrong. Please try again.',
} as const;
