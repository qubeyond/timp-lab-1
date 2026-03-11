export interface User {
    id: string;
    username: string;
}

export interface Post {
    id: string;
    owner_id: string;

    title: string;
    body: string;
    created_at: string;
}