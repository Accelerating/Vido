import { createContext, useContext, useState, type ReactNode } from "react";
import { translations, type Lang } from "./translations";

function getInitialLang(): Lang {
  const stored = localStorage.getItem("vido-lang");
  if (stored === "zh" || stored === "en") return stored;
  return "en";
}

interface I18nContextType {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: keyof typeof translations.zh) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getInitialLang);

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem("vido-lang", l);
  };

  const t = (key: keyof typeof translations.zh) => translations[lang][key];

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useT() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useT must be within I18nProvider");
  return ctx;
}
