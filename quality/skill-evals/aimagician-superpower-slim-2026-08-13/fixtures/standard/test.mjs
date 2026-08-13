import assert from "node:assert/strict";
import { formatGreeting } from "./src/greeting.mjs";

assert.equal(formatGreeting("Ada"), "Hello, Ada!");
assert.equal(formatGreeting(" Ada "), "Hello, Ada!");
assert.equal(formatGreeting("Ada", { punctuation: "?" }), "Hello, Ada?");
assert.equal(formatGreeting("Ada", { punctuation: "." }), "Hello, Ada.");
assert.throws(() => formatGreeting("Ada", { punctuation: "!".repeat(2) }), TypeError);
assert.throws(() => formatGreeting("Ada", { punctuation: ":" }), TypeError);
assert.throws(() => formatGreeting("Ada", { punctuation: 1 }), TypeError);
console.log("standard-fixture: PASS");
