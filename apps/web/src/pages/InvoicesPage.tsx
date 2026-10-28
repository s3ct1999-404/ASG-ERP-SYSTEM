import { ResourceState } from "@/components/ResourceState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import { fiscalLabel } from "@/lib/fiscal";
import { useResource } from "@/lib/useResource";

export function InvoicesPage() {
  const { tenantId } = useAuth();
  const invoices = useResource(api.invoices, tenantId);
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Sales invoices</h1>
      <Card>
        <CardHeader>
          <CardTitle>Invoices</CardTitle>
          <CardDescription>
            Internal status and fiscal status are separate. An invoice is only "Fiscalised" when the
            tax authority has confirmed it. Creating invoices from this screen is not built yet (API
            only).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResourceState resource={invoices} emptyText="No invoices yet.">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Number</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Paid</TableHead>
                    <TableHead>Fiscal status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((i) => {
                    const f = fiscalLabel(i.fiscal_status);
                    return (
                      <TableRow key={i.id}>
                        <TableCell>{i.number}</TableCell>
                        <TableCell>{i.date}</TableCell>
                        <TableCell>{i.channel}</TableCell>
                        <TableCell>{i.status}</TableCell>
                        <TableCell>{i.total}</TableCell>
                        <TableCell>{i.amount_paid}</TableCell>
                        <TableCell>
                          <Badge variant={f.variant} title={f.note}>
                            {f.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </ResourceState>
        </CardContent>
      </Card>
    </div>
  );
}
