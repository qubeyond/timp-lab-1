export interface PostResponse {
    id: string;
    owner_id: string | null;
    title: string;
    body: string;
    created_at: string;
    updated_at: string;
}

export interface PostCreate {
    title: string;
    body: string;
}

export interface PostUpdate {
    title?: string;
    body?: string;
    is_published?: boolean;
}