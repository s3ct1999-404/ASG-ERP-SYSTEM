import { useRef, useState, type FormEvent } from "react";
import { ResourceState } from "@/components/ResourceState";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/api";
import { useAuth } from "@/auth";
import { useResource } from "@/lib/useResource";

const QTY = /^\d{1,14}(\.\d{1,4})?$/; // UX hint only; the server validates authoritatively.

export function StockPage() {
  const { tenantId } = useAuth();
  const stock = useResource(api.stock, tenantId);
  const warehouses = useResource(api.warehouses, tenantId);
  const products = useResource(api.products, tenantId);
  const [warehouse, setWarehouse] = useState("");
  const [product, setProduct] = useState("");
  const [qty, setQty] = useState("");
  const [cost, setCost] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // One key per logical submission: reused on retry (so a lost response cannot double-receive),
  // renewed only after the server confirms success.
  const idemKey = useRef<string>(crypto.randomUUID());

  const stocked = (products.data ?? []).filter((p) => p.is_service === false);
  const warehouseId = warehouse || warehouses.data?.[0]?.id || "";
  const productId = product || stocked[0]?.id || "";
  const valid = Boolean(
    warehouseId && productId && QTY.test(qty) && Number(qty) > 0 && QTY.test(cost),
  );

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const r = await api.receiveStock({
        warehouse: warehouseId,
        product: productId,
        qty,
        unit_cost: cost,
        idempotency_key: idemKey.current,
      });
      setNotice(
        r.replayed
          ? "This receipt was already recorded; nothing was added twice."
          : `Received ${r.qty} @ ${r.unit_cost}.`,
      );
      idemKey.current = crypto.randomUUID();
      setQty("");
      setCost("");
      stock.reload();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not receive stock. You can retry safely.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Stock</h1>
      <Card>
        <CardHeader>
          <CardTitle>Receive stock</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2" noValidate>
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-wh">Warehouse</Label>
              <Select id="r-wh" value={warehouseId} onChange={(e) => setWarehouse(e.target.value)}>
                {(warehouses.data ?? []).map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.code} - {w.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-prod">Product</Label>
              <Select id="r-prod" value={productId} onChange={(e) => setProduct(e.target.value)}>
                {stocked.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} - {p.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-qty">Quantity</Label>
              <Input
                id="r-qty"
                inputMode="decimal"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-cost">Unit cost</Label>
              <Input
                id="r-cost"
                inputMode="decimal"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
              />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={!valid || busy}>
                {busy ? "Receiving..." : "Receive stock"}
              </Button>
            </div>
            {error && (
              <Alert variant="destructive" className="sm:col-span-2">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {notice && (
              <p role="status" className="text-sm sm:col-span-2">
                {notice}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Balances</CardTitle>
        </CardHeader>
        <CardContent>
          <ResourceState resource={stock} emptyText="No stock on hand yet.">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Warehouse</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Qty</TableHead>
                    <TableHead>Avg cost</TableHead>
                    <TableHead>Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((r) => (
                    <TableRow key={`${r.warehouse}-${r.sku}`}>
                      <TableCell>{r.warehouse}</TableCell>
                      <TableCell>{r.sku}</TableCell>
                      <TableCell>{r.qty}</TableCell>
                      <TableCell>{r.avg_cost}</TableCell>
                      <TableCell>{r.value}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </ResourceState>
        </CardContent>
      </Card>
    </div>
  );
}
