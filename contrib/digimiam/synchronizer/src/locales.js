import Vue from 'vue'
import VueI18n from 'vue-i18n'

Vue.use(VueI18n)

const locales = {
  en: {
    warning: 'Warning:',
    info: 'Info:',
    activate: 'ACTIVATE',
    dish_generator_matrix: 'DISH GENERATOR MATRIX',
    digimiam_menu: 'DIGIMIAM MENU',
    α: 'α',
    Ω: 'Ω',
    β_minus: 'β-',
    β_plus: 'β+',
    start_manual_synchronization: 'START MANUAL SYNCHRONIZATION',
    devices_synchronization: 'DEVICES SYNCHRONIZATION',
    hashtag_hashtag_error: '## Error ##',
    steakfie: 'Steakfie',
    pizzage: 'Pizzage',
    gaufresque: 'Gaufresque',
    puddy_puddy: 'Puddy puddy',
    insectosteak: 'Insectosteak',
    pizzaliere: 'Pizzalière',
    spider_gaufre: 'Spider-gaufre',
    potjevleesch: 'PotjeVleesch',
    protobulle: 'Protobulle',
    cambraisienne: 'Cambraisienne',
    nano_gaufre: 'Nano-gaufre',
    chtite_gelee: 'Ch\'tite gelée',
    salade_flamande: 'Salade Flamande',
    pizzalgue: 'Pizzalgue',
    gaufre_fouret: 'Gaufre fourêt',
    flubber: 'Flubber',
  },
  fr: {
    warning: 'Attention:',
    info: 'Info:',
    activate: 'ACTIVER',
    dish_generator_matrix: 'MATRICE GÉNÉRATRICE DE PLATS',
    digimiam_menu: 'MENU DU DIGIMIAM',
    α: 'α',
    Ω: 'Ω',
    β_minus: 'β-',
    β_plus: 'β+',
    start_manual_synchronization: 'DÉMARRER LA SYNCHRO. MANUELLE',
    devices_synchronization: 'SYNCHRONISATION DES SYSTÈMES',
    hashtag_hashtag_error: '## Erreur ##',
    steakfie: 'Steakfie',
    pizzage: 'Pizzage',
    gaufresque: 'Gaufresque',
    puddy_puddy: 'Puddy puddy',
    insectosteak: 'Insectosteak',
    pizzaliere: 'Pizzalière',
    spider_gaufre: 'Spider-gaufre',
    potjevleesch: 'PotjeVleesch',
    protobulle: 'Protobulle',
    cambraisienne: 'Cambraisienne',
    nano_gaufre: 'Nano-gaufre',
    chtite_gelee: 'Ch\'tite gelée',
    salade_flamande: 'Salade Flamande',
    pizzalgue: 'Pizzalgue',
    gaufre_fouret: 'Gaufre fourêt',
    flubber: 'Flubber',
  }
}

const i18n = new VueI18n({
  locale: 'fr',
  messages: locales,
})

export default i18n
