import { Navigate } from "react-router-dom";
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

  // Skip the marketing page for users who are already signed in.
  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main-content" className="skip-link">
        Saltar al contenido principal
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
