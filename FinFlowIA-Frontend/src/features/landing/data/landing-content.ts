import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck,
  BarChart3,
  FileDown,
  Layers,
  ShieldCheck,
  Smartphone,
  Sparkles,
  UserPlus,
  Wallet,
} from "lucide-react";

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FEATURES: Feature[] = [
  {
    icon: Sparkles,
    title: "Categorización automática con IA",
    description:
      "Cada movimiento se analiza y clasifica solo, con un motor de IA entrenado para el lenguaje de los pequeños negocios. Vos revisás, no tipeás.",
  },
  {
    icon: BarChart3,
    title: "Dashboard en tiempo real",
    description:
      "Ingresos, gastos y balance del mes de un vistazo, con el detalle por categoría siempre actualizado apenas cargás un movimiento.",
  },
  {
    icon: FileDown,
    title: "Reportes exportables",
    description:
      "Generá reportes en CSV o PDF listos para compartir con tu contador o tu equipo, filtrados por el período que necesites.",
  },
  {
    icon: Layers,
    title: "Categorías a tu medida",
    description:
      "Empezá con las categorías predefinidas y sumá las propias cuando tu negocio lo necesite — vos decidís cómo se organizan tus finanzas.",
  },
  {
    icon: ShieldCheck,
    title: "Seguridad de nivel bancario",
    description:
      "Autenticación con JWT, contraseñas con hashing bcrypt y comunicación cifrada. Tus datos financieros, protegidos en cada paso.",
  },
  {
    icon: Smartphone,
    title: "Donde estés, como quieras",
    description:
      "Una interfaz responsive pensada para que cargues un gasto desde el celular en el momento, y revises los números desde la computadora.",
  },
];

export interface Step {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const STEPS: Step[] = [
  {
    icon: UserPlus,
    title: "Creá tu cuenta",
    description: "Registrate en menos de un minuto. Sin tarjeta, sin vueltas.",
  },
  {
    icon: Wallet,
    title: "Cargá tus movimientos",
    description: "Registrá cada ingreso y gasto con una descripción y un monto.",
  },
  {
    icon: Sparkles,
    title: "Dejá que la IA categorice",
    description: "En segundos, cada transacción queda clasificada automáticamente.",
  },
  {
    icon: BarChart3,
    title: "Mirá tu negocio con claridad",
    description: "Dashboard y reportes siempre al día, sin planillas manuales.",
  },
];

export interface TrustIndicator {
  icon: LucideIcon;
  title: string;
  description: string;
}

/**
 * FinFlowIA todavía no tiene clientes públicos, así que en vez de inventar
 * testimonios con nombres y fotos falsas, esta sección muestra señales de
 * confianza reales sobre cómo está construido el producto. Reemplazar por
 * testimonios reales cuando existan.
 */
export const TRUST_INDICATORS: TrustIndicator[] = [
  {
    icon: Sparkles,
    title: "Impulsado por Claude (Anthropic)",
    description: "La misma familia de modelos de IA usada por miles de empresas.",
  },
  {
    icon: ShieldCheck,
    title: "Cifrado extremo a extremo",
    description: "Tus credenciales y movimientos viajan siempre cifrados.",
  },
  {
    icon: BadgeCheck,
    title: "Pensado para pequeños negocios",
    description: "Diseñado desde cero para quienes llevan sus cuentas solos.",
  },
];

export interface FAQItem {
  question: string;
  answer: string;
}

export const FAQ_ITEMS: FAQItem[] = [
  {
    question: "¿Necesito tarjeta de crédito para empezar?",
    answer:
      "No. Podés crear tu cuenta y empezar a cargar movimientos sin ingresar ningún medio de pago.",
  },
  {
    question: "¿Cómo funciona la categorización con inteligencia artificial?",
    answer:
      "Cuando cargás una transacción sin elegir una categoría, el sistema envía la descripción y el monto a un modelo de lenguaje que la clasifica automáticamente en la categoría más adecuada, con un nivel de confianza asociado.",
  },
  {
    question: "¿Mis datos financieros están seguros?",
    answer:
      "Sí. Las contraseñas se guardan con hashing bcrypt, la sesión se maneja con JWT de corta duración y toda la comunicación con el servidor va cifrada.",
  },
  {
    question: "¿Puedo exportar mis reportes?",
    answer:
      "Sí, podés generar reportes filtrados por período y exportarlos en CSV o PDF para compartirlos con tu contador o tu equipo.",
  },
  {
    question: "¿Sirve para cualquier tipo de negocio?",
    answer:
      "FinFlowIA está pensado para pequeños negocios y profesionales independientes. Las categorías predefinidas cubren los casos más comunes, y podés sumar las tuyas propias si tu negocio lo necesita.",
  },
  {
    question: "¿Puedo usarlo desde el celular?",
    answer:
      "Sí, la aplicación es completamente responsive: podés cargar un gasto apenas lo hacés y revisar tu dashboard desde cualquier dispositivo.",
  },
];

export const NAV_LINKS = [
  { label: "Características", href: "#features" },
  { label: "Cómo funciona", href: "#how-it-works" },
  { label: "Preguntas frecuentes", href: "#faq" },
] as const;

export const FOOTER_LINKS = {
  producto: [
    { label: "Características", href: "#features" },
    { label: "Cómo funciona", href: "#how-it-works" },
    { label: "Preguntas frecuentes", href: "#faq" },
  ],
  cuenta: [
    { label: "Iniciar sesión", href: "/login" },
    { label: "Crear cuenta", href: "/register" },
  ],
  legal: [
    { label: "Privacidad", href: "#" },
    { label: "Términos de servicio", href: "#" },
  ],
} as const;
