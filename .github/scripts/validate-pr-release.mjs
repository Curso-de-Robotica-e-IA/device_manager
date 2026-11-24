import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import {
  readProjectVersion,
  validatePullRequestRelease,
} from "./release-policy.mjs";

const targetBranch = process.env.BASE_REF;
const body = process.env.PR_BODY ?? "";

if (targetBranch !== "main" && targetBranch !== "dev") {
  throw new Error(`Unsupported PR target '${targetBranch}'.`);
}

const basePyproject = execFileSync(
  "git",
  ["show", `origin/${targetBranch}:pyproject.toml`],
  { encoding: "utf8" },
);
const headPyproject = readFileSync("pyproject.toml", "utf8");
const result = validatePullRequestRelease({
  body,
  baseVersion: readProjectVersion(basePyproject),
  headVersion: readProjectVersion(headPyproject),
  targetBranch,
});

console.log(`Validated ${result.impact} release version ${result.version} for ${targetBranch}.`);
