#!/usr/bin/env node

// SessionStart hook. prompts/system-prompt.md의 규칙 블록을 세션에 넣습니다.
// 구조는 AminBlg/SimpleEnglish의 simple-english-activate.js(MIT)를 가져와 바꿨습니다.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

// Claude Code는 hook 출력을 10,000자에서 자릅니다. 넘으면 파일로 보내고
// 미리보기만 모델에 주므로 hook이 뜻을 잃습니다.
const MAX_CHARS = 9500;

const STYLE_NAME = 'simple-korean';

const FALLBACK_CONTEXT = `SIMPLE KOREAN 규칙이 자동으로 켜졌습니다.

한 번 읽고 이해하는 한국어로 쓴다. "~합니다" 체. 한 문장에 새 정보 하나. 능동형, 행위자 명시. 번역투 금지. em-dash와 세미콜론 금지. 기술 용어는 영어 그대로. 답변은 첫 문장이 답, 여닫는 말 금지, 서식은 비교하거나 셀 때만. 코드, 식별자, 명령어, 인용 에러는 건드리지 않는다.`;

const HEADER = [
  'SIMPLE KOREAN 규칙이 자동으로 켜졌습니다.',
  '',
  '사용자가 스킬 이름을 말하지 않아도 아래 규칙을 따른다. 전체 규칙은 이 플러그인의 skills/simple-korean/SKILL.md에 있다. 점검이 필요하면 그 파일을 읽는다.',
  '',
].join('\n');

const STYLE_ACTIVE_NOTICE = `simple-korean output style이 켜져 있어 hook은 규칙을 다시 넣지 않습니다. 둘 중 하나만 쓰세요.`;

function candidates(pluginRoot, hookDirectory, relative) {
  const roots = [];
  if (pluginRoot) {
    roots.push(pluginRoot);
  }
  roots.push(path.join(hookDirectory, '..', '..'), path.join(hookDirectory, '..'));
  return roots.map((root) => path.join(root, ...relative));
}

function promptCandidates(pluginRoot, hookDirectory) {
  return candidates(pluginRoot, hookDirectory, ['prompts', 'system-prompt.md']);
}

function readFirstFile(list) {
  for (const candidate of list) {
    try {
      return fs.readFileSync(candidate, 'utf8');
    } catch (error) {
      // 없거나 읽을 수 없거나 디렉터리면 다음 후보로 넘어갑니다.
    }
  }
  return '';
}

function stripFrontmatter(content) {
  return content.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '');
}

// prompts/system-prompt.md는 사람이 읽는 페이지입니다. 제목, 붙이는 곳 안내,
// 두 "---" 사이의 규칙 블록, 짧은 판본 순서입니다. 모델에게는 규칙 블록만 줍니다.
function ruleBlock(content) {
  const fence = /^---[ \t]*\r?$/m;
  const first = content.search(fence);
  if (first === -1) {
    return content;
  }
  const rest = content.slice(first).replace(fence, '');
  const second = rest.search(fence);
  return second === -1 ? rest : rest.slice(0, second);
}

// 설정 파일에서 outputStyle 값을 읽습니다. 사용자 설정, 프로젝트 설정,
// 프로젝트 로컬 설정을 모두 봅니다. 하나라도 simple-korean이면 켜진 것으로 봅니다.
function settingsCandidates(env, cwd) {
  const configDir = env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  return [
    path.join(configDir, 'settings.json'),
    path.join(cwd, '.claude', 'settings.json'),
    path.join(cwd, '.claude', 'settings.local.json'),
  ];
}

function outputStyleActive(settingsPaths) {
  for (const file of settingsPaths) {
    let text;
    try {
      text = fs.readFileSync(file, 'utf8');
    } catch (error) {
      continue;
    }
    try {
      const style = JSON.parse(text).outputStyle;
      if (typeof style === 'string' && style.split(':').pop() === STYLE_NAME) {
        return true;
      }
    } catch (error) {
      // JSON이 깨진 설정 파일은 건너뜁니다.
    }
  }
  return false;
}

function buildContext(promptText) {
  if (!promptText) {
    return FALLBACK_CONTEXT;
  }
  const out = HEADER + ruleBlock(stripFrontmatter(promptText)).trim();
  if (out.length > MAX_CHARS) {
    process.stderr.write(`simple-korean hook: 규칙 블록이 ${out.length}자로 상한 ${MAX_CHARS}자를 넘어 짧은 판본을 보냅니다\n`);
    return FALLBACK_CONTEXT;
  }
  return out;
}

function main() {
  if (outputStyleActive(settingsCandidates(process.env, process.cwd()))) {
    process.stdout.write(STYLE_ACTIVE_NOTICE);
    return;
  }
  const pluginRoot = process.env.PLUGIN_ROOT || process.env.CLAUDE_PLUGIN_ROOT;
  process.stdout.write(buildContext(readFirstFile(promptCandidates(pluginRoot, __dirname))));
}

if (require.main === module) {
  main();
}

module.exports = {
  FALLBACK_CONTEXT,
  MAX_CHARS,
  STYLE_ACTIVE_NOTICE,
  STYLE_NAME,
  buildContext,
  outputStyleActive,
  promptCandidates,
  readFirstFile,
  ruleBlock,
  settingsCandidates,
  stripFrontmatter,
};
