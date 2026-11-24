const releaseOptions = /^\s*-\s*\[([ xX])\]\s*`?(patch|minor|major)`?(?:\s*[—-].*)?\s*$/gim;
const versionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:b([1-9]\d*))?$/;

export function readProjectVersion(pyproject) {
  let inProjectSection = false;

  for (const line of pyproject.split(/\r?\n/)) {
    if (line.startsWith("[") && line.endsWith("]")) {
      if (inProjectSection) {
        break;
      }
      inProjectSection = line === "[project]";
      continue;
    }

    if (inProjectSection) {
      const match = line.match(/^version\s*=\s*"([^"]+)"\s*$/);
      if (match) {
        return match[1];
      }
    }
  }

  throw new Error("Could not find project.version in pyproject.toml.");
}

export function selectedReleaseImpact(body) {
  const choices = [...body.matchAll(releaseOptions)];
  const selected = choices
    .filter(([, checked]) => checked.toLowerCase() === "x")
    .map(([, , impact]) => impact.toLowerCase());

  if (selected.length !== 1) {
    throw new Error("Select exactly one release impact: patch, minor, or major.");
  }

  return selected[0];
}

function parseVersion(version) {
  const match = version.match(versionPattern);
  if (!match) {
    throw new Error(`Unsupported release version '${version}'. Use X.Y.Z or X.Y.ZbN.`);
  }

  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    beta: match[4] === undefined ? undefined : Number(match[4]),
  };
}

function formatVersion({ major, minor, patch, beta }) {
  const stable = `${major}.${minor}.${patch}`;
  return beta === undefined ? stable : `${stable}b${beta}`;
}

function incrementStable(version, impact) {
  const { major, minor, patch } = version;

  if (impact === "major") {
    return { major: major + 1, minor: 0, patch: 0 };
  }
  if (impact === "minor") {
    return { major, minor: minor + 1, patch: 0 };
  }
  return { major, minor, patch: patch + 1 };
}

export function expectedReleaseVersion(baseVersion, impact, targetBranch) {
  if (!["patch", "minor", "major"].includes(impact)) {
    throw new Error(`Unsupported release impact '${impact}'.`);
  }

  const base = parseVersion(baseVersion);

  if (targetBranch === "main") {
    if (base.beta !== undefined) {
      throw new Error("The main branch must be based on a stable version.");
    }
    return formatVersion(incrementStable(base, impact));
  }

  if (targetBranch !== "dev") {
    throw new Error(`Unsupported release target '${targetBranch}'.`);
  }

  if (base.beta === undefined) {
    return formatVersion({ ...incrementStable(base, impact), beta: 1 });
  }

  if (impact === "patch") {
    return formatVersion({ ...base, beta: base.beta + 1 });
  }

  return formatVersion({ ...incrementStable(base, impact), beta: 1 });
}

export function validatePullRequestRelease({ body, baseVersion, headVersion, targetBranch }) {
  const impact = selectedReleaseImpact(body);
  const expectedVersion = expectedReleaseVersion(baseVersion, impact, targetBranch);

  if (headVersion !== expectedVersion) {
    throw new Error(
      `The selected ${impact} update requires version ${expectedVersion} on ${targetBranch}; ` +
        `pyproject.toml contains ${headVersion}.`,
    );
  }

  return { impact, version: expectedVersion };
}
