import { useState, type FormEvent } from "react";
import { ResourceState } from "@/components/ResourceState";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
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

const PRICE = /^\d{1,18}(\.\d{1,2})?$/; // UX hint only; the server validates authoritatively.

export function ProductsPage() {
  const { tenantId } = useAuth();
  const products = useResource(api.products, tenantId);
  const companies = useResource(api.companies, tenantId);
  const uoms = useResource(api.uoms, tenantId);
  const [company, setCompany] = useState("");
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [uom, setUom] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const companyId = company || companies.data?.[0]?.id || "";
  const uomId = uom || uoms.data?.[0]?.id || "";
  const valid = Boolean(companyId && uomId && sku.trim() && name.trim() && PRICE.test(price));

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      const p = await api.createProduct({
        company: companyId,
        sku: sku.trim(),
        name: name.trim(),
        uom: uomId,
        sale_price: price,
      });
      setSaved(`Created ${p.sku}`);
      setSku("");
      setName("");
      setPrice("");
      products.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the product.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Products</h1>
      <Card>
        <CardHeader>
          <CardTitle>New product</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2" noValidate>
            <div className="flex flex-col gap-2">
              <Label htmlFor="p-company">Company</Label>
              <Select id="p-company" value={companyId} onChange={(e) => setCompany(e.target.value)}>
                {(companies.data ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="p-uom">Unit of measure</Label>
              <Select id="p-uom" value={uomId} onChange={(e) => setUom(e.target.value)}>
                {(uoms.data ?? []).map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.code} - {u.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="p-sku">SKU</Label>
              <Input
                id="p-sku"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                maxLength={50}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="p-name">Name</Label>
              <Input
                id="p-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={200}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="p-price">Sale price</Label>
              <Input
                id="p-price"
                inputMode="decimal"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                aria-invalid={price !== "" && !PRICE.test(price)}
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" disabled={!valid || busy}>
                {busy ? "Saving..." : "Create product"}
              </Button>
            </div>
            {error && (
              <Alert variant="destructive" className="sm:col-span-2">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {saved && (
              <p role="status" className="text-sm sm:col-span-2">
                {saved}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Catalogue</CardTitle>
        </CardHeader>
        <CardContent>
          <ResourceState resource={products} emptyText="No products yet. Create one above.">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.sku}</TableCell>
                      <TableCell>{p.name}</TableCell>
                      <TableCell>{p.sale_price}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{p.is_service ? "Service" : "Stocked"}</Badge>
                      </TableCell>
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
