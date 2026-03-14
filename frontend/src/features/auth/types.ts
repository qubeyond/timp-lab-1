export interface UserResponse {
    id: string;
    username: string;
    created_at: string;
    last_login: string | null;
    is_deleted: boolean;
}

export interface UserCreate {
    username: string;
    password: string;
}

export interface Token {
    access_token: string;
    token_type: string;
}