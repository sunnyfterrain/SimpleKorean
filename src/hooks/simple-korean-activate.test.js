const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const hook = require('./simple-korean-activate.js');

const ROOT = path.join(__dirname, '..', '..');

test('ruleBlock은 두 --- 사이의 내용만 돌려준다', () => {
  const page = '# 제목\n\n안내문\n\n---\n\n규칙 A\n규칙 B\n\n---\n\n## 짧은 판본\n짧은 글';
  assert.equal(hook.ruleBlock(page).trim(), '규칙 A\n규칙 B');
});

test('ruleBlock은 fence가 없으면 전체를 돌려준다', () => {
  assert.equal(hook.ruleBlock('규칙만'), '규칙만');
});

test('stripFrontmatter는 frontmatter를 지운다', () => {
  assert.equal(hook.stripFrontmatter('---\nname: x\n---\n본문'), '본문');
});

test('buildContext는 빈 입력에 fallback을 준다', () => {
  assert.equal(hook.buildContext(''), hook.FALLBACK_CONTEXT);
});

test('buildContext는 상한을 넘으면 fallback을 준다', () => {
  const big = '# 제목\n\n---\n' + '가'.repeat(hook.MAX_CHARS + 1) + '\n---\n';
  assert.equal(hook.buildContext(big), hook.FALLBACK_CONTEXT);
});

test('실제 system-prompt.md는 상한 안에 들어가고 머리말이 붙는다', () => {
  const text = fs.readFileSync(path.join(ROOT, 'prompts', 'system-prompt.md'), 'utf8');
  const out = hook.buildContext(text);
  assert.ok(out.startsWith('SIMPLE KOREAN 규칙이 자동으로 켜졌습니다.'));
  assert.ok(out.includes('한 문장에 새 정보 하나'));
  assert.ok(!out.includes('짧은 판본'));
  assert.ok(out.length <= hook.MAX_CHARS);
});

test('promptCandidates는 플러그인 루트를 먼저 본다', () => {
  const list = hook.promptCandidates('/plugin', '/plugin/src/hooks');
  assert.equal(list[0], path.join('/plugin', 'prompts', 'system-prompt.md'));
});

test('readFirstFile은 없는 파일을 건너뛴다', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-'));
  const good = path.join(dir, 'good.md');
  fs.writeFileSync(good, '내용');
  assert.equal(hook.readFirstFile([path.join(dir, 'none.md'), good]), '내용');
});

function withSettings(json) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-settings-'));
  const file = path.join(dir, 'settings.json');
  fs.writeFileSync(file, json);
  return file;
}

test('outputStyleActive는 simple-korean이 설정되면 true', () => {
  assert.equal(hook.outputStyleActive([withSettings('{"outputStyle":"simple-korean"}')]), true);
});

test('outputStyleActive는 플러그인 접두어가 붙은 이름도 인식한다', () => {
  assert.equal(hook.outputStyleActive([withSettings('{"outputStyle":"simple-korean:simple-korean"}')]), true);
});

test('outputStyleActive는 다른 style, 없는 파일, 깨진 JSON에 false', () => {
  assert.equal(hook.outputStyleActive([
    '/nonexistent/settings.json',
    withSettings('{"outputStyle":"simple-english"}'),
    withSettings('{broken'),
  ]), false);
});

test('settingsCandidates는 CLAUDE_CONFIG_DIR를 먼저 본다', () => {
  const list = hook.settingsCandidates({ CLAUDE_CONFIG_DIR: '/cfg' }, '/proj');
  assert.equal(list[0], path.join('/cfg', 'settings.json'));
  assert.equal(list[1], path.join('/proj', '.claude', 'settings.json'));
});
