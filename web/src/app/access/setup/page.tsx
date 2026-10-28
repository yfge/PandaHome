import { Protected } from "@/components/auth/protected";
import { AccessSetupGuide } from "@/components/access/setup-guide";

export default function AccessSetupPage() {
  return <Protected>
    <AccessSetupGuide />
  </Protected>;
}
