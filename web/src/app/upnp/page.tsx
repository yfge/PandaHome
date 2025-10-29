import { Protected } from "@/components/auth/protected";

import { UpnpPageClient } from "./page-client";

export default function UpnpPage() {
  return (
    <Protected>
      <UpnpPageClient />
    </Protected>
  );
}
