import assert from "node:assert/strict";

import { canRenderDeleteAccountAction } from "./deleteVisibility.js";

assert.equal(canRenderDeleteAccountAction("admin"), true);
assert.equal(canRenderDeleteAccountAction("head_coach"), false);
assert.equal(canRenderDeleteAccountAction("coach"), false);
assert.equal(canRenderDeleteAccountAction("captain"), false);
assert.equal(canRenderDeleteAccountAction(null), false);
