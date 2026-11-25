import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import commonEs from "./locales/es/common.json";
import navEs from "./locales/es/nav.json";
import authEs from "./locales/es/auth.json";
import landingEs from "./locales/es/landing.json";
import dashboardEs from "./locales/es/dashboard.json";
import transactionsEs from "./locales/es/transactions.json";
import reportsEs from "./locales/es/reports.json";
import productsEs from "./locales/es/products.json";

import commonEn from "./locales/en/common.json";
import navEn from "./locales/en/nav.json";
import authEn from "./locales/en/auth.json";
import landingEn from "./locales/en/landing.json";
import dashboardEn from "./locales/en/dashboard.json";
import transactionsEn from "./locales/en/transactions.json";
import reportsEn from "./locales/en/reports.json";
import productsEn from "./locales/en/products.json";

export const defaultNS = "common";

export const resources = {
  es: {
    common: commonEs,
    nav: navEs,
    auth: authEs,
    landing: landingEs,
    dashboard: dashboardEs,
    transactions: transactionsEs,
    reports: reportsEs,
    products: productsEs,
  },
  en: {
    common: commonEn,
    nav: navEn,
    auth: authEn,
    landing: landingEn,
    dashboard: dashboardEn,
    transactions: transactionsEn,
    reports: reportsEn,
    products: productsEn,
  },
} as const;

// FinFlowIA targets Spanish-speaking small businesses first, so Spanish is
// the default and fallback language; English is offered as a secondary
// option via the language switcher (persisted in localStorage under
// "finflowia-language" by the browser language detector below).
void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    defaultNS,
    fallbackLng: "es",
    supportedLngs: ["es", "en"],
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "finflowia-language",
      caches: ["localStorage"],
    },
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

// Keep <html lang="..."> in sync so screen readers use the right
// pronunciation/voice rules for the active language (accessibility).
function syncHtmlLang(lng: string): void {
  document.documentElement.lang = lng;
}
i18n.on("languageChanged", syncHtmlLang);
if (i18n.resolvedLanguage) {
  syncHtmlLang(i18n.resolvedLanguage);
}

export default i18n;
