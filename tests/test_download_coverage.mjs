import test from 'node:test';
import assert from 'node:assert/strict';
import {coversRequestedInterval} from '../scripts/coverage_guard.mjs';
const date=s=>new Date(s);
test('verified hash does NOT make October partial cache complete',()=>{
  const meta={from:'2026-10-01T00:00:00Z',to_exclusive:'2026-10-30T00:00:00Z',sha256:'valid-but-partial'};
  assert.equal(coversRequestedInterval(meta,date('2026-10-01'),date('2026-10-31')),false);
  assert.equal(coversRequestedInterval(meta,date('2026-10-01'),date('2026-10-30')),true);
});
test('portfolio manifests with to field also refresh when new Friday needed',()=>{
  const meta={from:'2026-10-01T00:00:00Z',to:'2026-10-30T00:00:00Z'};
  assert.equal(coversRequestedInterval(meta,date('2026-10-01'),date('2026-10-31')),false);
});
test('exact complete October interval is accepted, not re-fetched',()=>{
  const meta={from:'2026-10-01T00:00:00Z',to_exclusive:'2026-10-31T00:00:00Z'};
  assert.equal(coversRequestedInterval(meta,date('2026-10-01'),date('2026-10-31')),true);
});
test('missing or invalid cached coverage is never silently accepted',()=>{
  assert.throws(()=>coversRequestedInterval({sha256:'123'},date('2026-10-01'),date('2026-10-31')));
  assert.throws(()=>coversRequestedInterval({from:'2026-10-31',to:'2026-10-01'},date('2026-10-01'),date('2026-10-31')));
});
