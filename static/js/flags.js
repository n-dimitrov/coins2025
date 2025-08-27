// Flags helper - returns emoji flag for a country name
// Exposed globally as window.getCountryFlag(country)
(function(window){
    const flags = {
        'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹', 'Spain': '🇪🇸',
        'Finland': '🇫🇮', 'Croatia': '🇭🇷', 'Luxembourg': '🇱🇺', 'Belgium': '🇧🇪',
        'Austria': '🇦🇹', 'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Greece': '🇬🇷',
        'Ireland': '🇮🇪', 'Slovenia': '🇸🇮', 'Slovakia': '🇸🇰', 'Estonia': '🇪🇪',
        'Latvia': '🇱🇻', 'Lithuania': '🇱🇹', 'Malta': '🇲🇹', 'Cyprus': '🇨🇾',
        'Monaco': '🇲🇨', 'Vatican City': '🇻🇦', 'San Marino': '🇸🇲', 'Andorra': '🇦🇩'
    };

    function getCountryFlag(country) {
        if (!country) return '🇪🇺';
        return flags[country] || '🇪🇺';
    }

    window.getCountryFlag = getCountryFlag;
})(window);
