export interface Position {
    x: number;
    y: number;
}

export interface ChampionState {
    position: Position;
    health: number;
    mana: number;
    level: number;
    items: number[];
    gold: number;
    cs: number;
    kills: number;
    deaths: number;
    assists: number;
}

export interface GameState {
    timestamp: number;
    blue_team: Record<string, ChampionState>;
    red_team: Record<string, ChampionState>;
    events: Array<{
        type: string;
        timestamp: number;
        details: Record<string, any>;
    }>;
}

export interface Participant {
    summoner_name: string;
    champion: string;
    team: 'blue' | 'red';
    position: string;
}

export interface ProcessedReplay {
    match_id: string;
    game_duration: number;
    timestamp: string;
    participants: Participant[];
    champion_pathing: Record<string, Array<{
        x: number;
        y: number;
        timestamp: number;
    }>>;
    game_states: GameState[];
}

export interface ReplayListItem {
    match_id: string;
    game_duration: number;
    timestamp: string;
    participant_count: number;
} 