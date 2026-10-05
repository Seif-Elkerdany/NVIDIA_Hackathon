import type { ApiClient, Decoder } from "../../lib/api";
import {
  decodeHistory,
  decodeProfile,
  type Patch,
  type Profile,
  type ProfilePage,
} from "./model";

export interface ProfileWireClient extends Pick<ApiClient, "get"> {
  patchProfile<T>(
    body: Patch,
    idempotencyKey: string,
    decode: Decoder<T>,
    signal?: AbortSignal,
  ): Promise<T>;
}
export interface ProfileApi {
  current(signal?: AbortSignal): Promise<Profile>;
  history(cursor: string | null, signal?: AbortSignal): Promise<ProfilePage>;
  version(id: string, signal?: AbortSignal): Promise<Profile>;
  save(
    body: Patch,
    idempotencyKey: string,
    signal?: AbortSignal,
  ): Promise<Profile>;
}
export function createProfileApi(client: ProfileWireClient): ProfileApi {
  return {
    current: (signal) => client.get("/api/v1/profile", decodeProfile, signal),
    history: (cursor, signal) =>
      client.get(
        `/api/v1/profile/versions?${new URLSearchParams({ limit: "20", ...(cursor ? { cursor } : {}) })}`,
        decodeHistory,
        signal,
      ),
    version: (id, signal) => {
      if (
        !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
          id,
        )
      )
        throw new Error("A profile version requires a UUID.");
      return client.get(
        `/api/v1/profile/versions/${id}`,
        decodeProfile,
        signal,
      );
    },
    save: (body, key, signal) =>
      client.patchProfile(body, key, decodeProfile, signal),
  };
}
