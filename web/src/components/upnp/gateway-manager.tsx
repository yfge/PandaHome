"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { GATEWAY_ENDPOINT, gatewayRequest, type UpnpGateway } from "@/components/upnp/gateway-api";
import { useGatewayTranslations } from "@/components/upnp/gateway-translations";
import { UpnpMappingList } from "@/components/upnp/mapping-list";
import { getErrorMessage } from "@/lib/api-client";

interface DiscoveryResult {
  gateways: UpnpGateway[];
  discovery_error: string | null;
}

export function UpnpGatewayManager() {
  const t = useGatewayTranslations();
  const [gateways, setGateways] = useState<UpnpGateway[]>([]);
  const [selected, setSelected] = useState<UpnpGateway | null>(null);
  const [deviceUrl, setDeviceUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [mappingBusy, setMappingBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [discovered, setDiscovered] = useState(false);

  const loadGateways = useCallback(async (refresh: boolean, signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const data = await gatewayRequest<DiscoveryResult>(`${GATEWAY_ENDPOINT}?refresh=${refresh}`, { signal });
      if (signal?.aborted) return;
      setGateways((current) => [...data.gateways, ...current.filter(
        (item) => !data.gateways.some((fresh) => fresh.device_url === item.device_url),
      )]);
      setSelected((current) => data.gateways.find((item) => item.device_url === current?.device_url) ?? current);
      setError(data.discovery_error);
      setDiscovered(true);
    } catch (cause) {
      if (!signal?.aborted) setError(getErrorMessage(cause, t("failed")));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const controller = new AbortController();
    void loadGateways(false, controller.signal);
    return () => controller.abort();
  }, [loadGateways]);

  const inspect = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const gateway = await gatewayRequest<UpnpGateway>(`${GATEWAY_ENDPOINT}/inspect`, {
        method: "POST", body: { device_url: deviceUrl.trim() },
      });
      setGateways((current) => [gateway, ...current.filter((item) => item.device_url !== gateway.device_url)]);
      setSelected(gateway);
    } catch (cause) {
      setError(getErrorMessage(cause, t("failed")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="min-w-0 space-y-4 p-6">
          <h2 className="text-lg font-semibold">{t("title")}</h2>
          <fieldset disabled={loading || mappingBusy} className="min-w-0 space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="grid min-w-0 flex-1 gap-2">
                <label htmlFor="upnp-gateway" className="text-sm font-medium">{t("router")}</label>
                <select id="upnp-gateway" value={selected?.device_url ?? ""}
                  className="border-input bg-background w-full min-w-0 max-w-full rounded-md border px-3 py-2 text-sm"
                  onChange={(event) => setSelected(gateways.find((item) => item.device_url === event.target.value) ?? null)}>
                  <option value="">{t("default")}</option>
                  {gateways.map((gateway) => (
                    <option key={gateway.device_url} value={gateway.device_url} disabled={!gateway.reachable}>
                      {gateway.name || gateway.host} ({gateway.host}){gateway.reachable ? "" : ` — ${t("unavailable")}`}
                    </option>
                  ))}
                </select>
              </div>
              <Button variant="outline" type="button" onClick={() => void loadGateways(true)}>{t("refresh")}</Button>
            </div>
            <form onSubmit={inspect} className="space-y-2">
              <label htmlFor="upnp-device-url" className="text-sm font-medium">{t("deviceUrl")}</label>
              <div className="flex flex-col gap-3 sm:flex-row">
                <Input id="upnp-device-url" type="url" required value={deviceUrl}
                  onChange={(event) => setDeviceUrl(event.target.value)}
                  placeholder="http://192.168.1.1:5000/rootDesc.xml" aria-describedby="upnp-device-url-help" />
                <Button type="submit" disabled={!deviceUrl.trim()}>{t("connect")}</Button>
              </div>
              <p id="upnp-device-url-help" className="text-muted-foreground text-sm">{t("help")}</p>
            </form>
          </fieldset>
          {loading ? <p role="status" className="text-muted-foreground text-sm">{t("loading")}</p> : null}
          {error ? <p role="alert" className="text-destructive text-sm">{error}</p> : null}
          {discovered && gateways.length === 0 ? <p className="text-muted-foreground text-sm">{t("empty")}</p> : null}
          {selected ? (
            <div className="bg-muted space-y-1 rounded-md p-3 text-sm" role="status">
              <p className="break-all font-medium">{selected.name || selected.host} · {selected.device_url}</p>
              <p>{t("wan", { address: selected.external_ip || t("unavailable") })}</p>
              <p>{t(selected.address_scope)}</p>
              {selected.error ? <p>{selected.error}</p> : null}
            </div>
          ) : null}
          <p className="text-muted-foreground text-sm">{t("layers")}</p>
        </CardContent>
      </Card>
      <fieldset disabled={loading} className="min-w-0">
        <UpnpMappingList key={selected?.device_url ?? "default"} deviceUrl={selected?.device_url} onBusyChange={setMappingBusy} />
      </fieldset>
    </div>
  );
}
