// Legacy schema values stay valid; only their display labels are translated.
const TYPE_LABELS = {
    角色: 'Character', character: 'Character',
    势力: 'Faction', faction: 'Faction',
    地点: 'Location', location: 'Location',
    法宝: 'Artifact', artifact: 'Artifact', item: 'Artifact',
}

export function entityTypeLabel(type) {
    return TYPE_LABELS[type] || TYPE_LABELS[String(type || '').toLowerCase()] || type || 'Unknown'
}
