export {
  buildPatch,
  decodeProfile,
  decodeHistory,
  initialEdits,
  validValue,
  fields,
  countries,
} from "../src/features/profile/model";
export { ProfileForm } from "../src/features/profile/ProfileScreen";
export { ValueText, FactSummary } from "../src/features/profile/Fields";
export { createProfileApi } from "../src/features/profile/api";
export { createApiClient, ApiError, ContractError } from "../src/lib/api";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";
import { ProfileForm } from "../src/features/profile/ProfileScreen";
import type { Profile } from "../src/features/profile/model";
export function renderProfile(profile: Profile) {
  return renderToStaticMarkup(
    <MemoryRouter>
      <ProfileForm
        profile={profile}
        pending={false}
        error={null}
        refreshing={false}
        onSave={() => {}}
        onReload={() => {}}
      />
    </MemoryRouter>,
  );
}
