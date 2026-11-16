// Canonical schema values have readable English display labels.
const TYPE_LABELS = {
    character: 'Character', faction: 'Faction', location: 'Location',
    artifact: 'Artifact', item: 'Item', technique: 'Technique',
}

export function entityTypeLabel(type) {
    return TYPE_LABELS[String(type || '').toLowerCase()] || type || 'Unknown'
}
