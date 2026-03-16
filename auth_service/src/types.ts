export interface AccountResponse {
  name: string;
  surname: string;
  email: string;
  sessionID?: string | null;
}

export interface QueryModule {
  accountLogin: (
    db: any,
    email: string,
    passwordHash: string
  ) => Promise<AccountResponse | null>;
  fetchSessionData: (db: any, sessionId: string) => Promise<AccountResponse | null>;
  insertUser: (
    db: any,
    name: string,
    surname: string,
    email: string,
    passwordHash: string
  ) => Promise<number | null>;
  insertSession: (db: any, userId: number, email?: string) => Promise<string | null>;
}
