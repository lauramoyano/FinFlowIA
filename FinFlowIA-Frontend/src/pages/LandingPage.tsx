import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { LandingNavbar } from "@/features/landing/components/LandingNavbar";
import { HeroSection } from "@/features/landing/components/HeroSection";
import { TrustSection } from "@/features/landing/components/TrustSection";
import { FeaturesSection } from "@/features/landing/components/FeaturesSection";
import { HowItWorksSection } from "@/features/landing/components/HowItWorksSection";
import { FAQSection } from "@/features/landing/components/FAQSection";
import { CTASection } from "@/features/landing/components/CTASection";
import { LandingFooter } from "@/features/landing/components/LandingFooter";

export function LandingPage() {
  const token = useAuthStore((state) => state.token);
  const { t } = useTranslation("landing");

  // Skip the marketing page for users who are already signed in.
  if (token) {
    return <Navigate to="/home" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main-content" className="skip-link">
        {t("skipToContent")}
      </a>
      <LandingNavbar />
      <main id="main-content" className="flex-1">
        <HeroSection />
        <TrustSection />
        <FeaturesSection />
        <HowItWorksSection />
        <FAQSection />
        <CTASection />
      </main>
      <LandingFooter />
    </div>
  );
}
