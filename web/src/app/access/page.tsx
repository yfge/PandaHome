import { Protected } from "@/components/auth/protected";

import { AccessPageClient } from "./page-client";

export default function AccessPage() {
  return <Protected>
    <AccessPageClient />
  </Protected>;
}
