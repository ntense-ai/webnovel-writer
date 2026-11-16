import test from 'node:test'
import assert from 'node:assert/strict'
import { buildForeshadowingRecords } from './foreshadowing.js'
import { entityTypeLabel } from './entityTypes.js'
import { formatNumber, formatChapterLabel, formatTableValue } from './format.js'

test('legacy and English foreshadowing fields share classifications and weights', () => {
    const records = buildForeshadowingRecords({
        progress: { current_chapter: 5 },
        plot_threads: { foreshadowing: [
            { tier: '核心', status: '已回收', planted_chapter: 1, target_chapter: 9 },
            { tier: 'core', status: 'resolved', planted_chapter: 1, target_chapter: 9 },
            { tier: '装饰', planted_chapter: 1, target_chapter: 9 },
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

test('legacy entity types render English without changing unknown user types', () => {
    for (const [legacy, modern, label] of [
        ['角色', 'character', 'Character'], ['势力', 'faction', 'Faction'],
        ['地点', 'location', 'Location'], ['法宝', 'artifact', 'Artifact'],
    ]) {
        assert.equal(entityTypeLabel(legacy), label)
        assert.equal(entityTypeLabel(modern), label)
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
