import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  expectedReleaseVersion,
  readProjectVersion,
  selectedReleaseImpact,
  validatePullRequestRelease,
} from "./release-policy.mjs";

function pullRequestBody(impact) {
  return [
    "- [ ] `patch` — compatible fix",
    "- [ ] `minor` — compatible feature",
    "- [ ] `major` — breaking change",
  ]
    .map((option) => option.replace(`[ ] \`${impact}\``, `[x] \`${impact}\``))
    .join("\n");
}

test("reads project.version from the project table", () => {
  const pyproject = [
    'name = "device_manager"',
    "[project]",
    'version = "0.5.0b2"',
    "[tool.poetry]",
    'version = "9.9.9"',
  ].join("\n");

  assert.equal(readProjectVersion(pyproject), "0.5.0b2");
});

test("requires exactly one checked release impact", () => {
  assert.equal(selectedReleaseImpact(pullRequestBody("minor")), "minor");
  assert.throws(() => selectedReleaseImpact(pullRequestBody("")), /exactly one/);
  assert.throws(() => selectedReleaseImpact(`${pullRequestBody("patch")}\n- [x] major`), /exactly one/);
});

test("recognizes the options in the pull request template", () => {
  const template = readFileSync(new URL("../PULL_REQUEST_TEMPLATE.md", import.meta.url), "utf8");
  const selectedTemplate = template.replace("- [ ] `patch`", "- [x] `patch`");

  assert.equal(selectedReleaseImpact(selectedTemplate), "patch");
});

test("calculates stable semantic version increments", () => {
  assert.equal(expectedReleaseVersion("0.4.2", "patch", "main"), "0.4.3");
  assert.equal(expectedReleaseVersion("0.4.2", "minor", "main"), "0.5.0");
  assert.equal(expectedReleaseVersion("0.4.2", "major", "main"), "1.0.0");
});

test("starts beta candidates from a stable version", () => {
  assert.equal(expectedReleaseVersion("0.4.2", "patch", "dev"), "0.4.3b1");
  assert.equal(expectedReleaseVersion("0.4.2", "minor", "dev"), "0.5.0b1");
  assert.equal(expectedReleaseVersion("0.4.2", "major", "dev"), "1.0.0b1");
});

test("increments the beta counter for another patch in the same candidate", () => {
  assert.equal(expectedReleaseVersion("0.5.0b2", "patch", "dev"), "0.5.0b3");
});

test("starts a new beta candidate when the impact increases", () => {
  assert.equal(expectedReleaseVersion("0.5.0b2", "minor", "dev"), "0.6.0b1");
  assert.equal(expectedReleaseVersion("0.5.0b2", "major", "dev"), "1.0.0b1");
});

test("rejects unsupported release impacts", () => {
  assert.throws(() => expectedReleaseVersion("0.4.2", "none", "main"), /Unsupported release impact/);
});

test("rejects mismatched selected impact and project version", () => {
  assert.throws(
    () =>
      validatePullRequestRelease({
        body: pullRequestBody("patch"),
        baseVersion: "0.4.2",
        headVersion: "0.5.0",
        targetBranch: "main",
      }),
    /requires version 0\.4\.3/,
  );
});
