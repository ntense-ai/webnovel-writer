import test from 'node:test'
import assert from 'node:assert/strict'
import { buildForeshadowingRecords } from './foreshadowing.js'
import { entityTypeLabel } from './entityTypes.js'
import { formatNumber, formatChapterLabel, formatTableValue } from './format.js'

test('Canonical and case-varied foreshadowing fields share classifications and weights', () => {
    const records = buildForeshadowingRecords({
        progress: { current_chapter: 5 },
        plot_threads: { foreshadowing: [
            { tier: 'CORE', status: 'RESOLVED', planted_chapter: 1, target_chapter: 9 },
            { tier: 'core', status: 'resolved', planted_chapter: 1, target_chapter: 9 },
            { tier: 'decorative', planted_chapter: 1, target_chapter: 9 },
            { tier: 'Decorative', planted_chapter: 1, target_chapter: 9 },
        ] },
    })
    for (const [a, b] of [[records[0], records[1]], [records[2], records[3]]]) {
        assert.equal(a.tier, b.tier)
        assert.equal(a.level, b.level)
        assert.equal(a.urgencyScore, b.urgencyScore)
    }
    assert.equal(records[0].statusText, 'Resolved')
    assert.equal(records[0].tier, 'Core')
    assert.equal(records[2].tier, 'Decorative')
})

test('Canonical entity types render English without changing unknown user types', () => {
    for (const [capitalized, canonical, label] of [
        ['Character', 'character', 'Character'], ['Faction', 'faction', 'Faction'],
        ['Location', 'location', 'Location'], ['Artifact', 'artifact', 'Artifact'],
    ]) {
        assert.equal(entityTypeLabel(capitalized), label)
        assert.equal(entityTypeLabel(canonical), label)
    }
    assert.equal(entityTypeLabel('Custom type'), 'Custom type')
    assert.equal(entityTypeLabel(null), 'Unknown')
})

test('dashboard formatters produce English labels and numbers', () => {
    assert.equal(formatNumber(12000), '12K')
    assert.equal(formatNumber(345), '345')
    assert.equal(formatChapterLabel(12), 'Chapter 12')
    assert.equal(formatTableValue(true), 'Yes')
    assert.equal(formatTableValue(false), 'No')
    assert.equal(formatTableValue(['a', 'b']), 'a, b')
})
