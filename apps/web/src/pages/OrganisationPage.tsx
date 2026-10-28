import { ResourceState } from "@/components/ResourceState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

export function OrganisationPage() {
  const { tenantId } = useAuth();
  const companies = useResource(api.companies, tenantId);
  const branches = useResource(api.branches, tenantId);
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Organisation</h1>
      <Card>
        <CardHeader>
          <CardTitle>Companies</CardTitle>
        </CardHeader>
        <CardContent>
          <ResourceState resource={companies} emptyText="No companies are visible to your role.">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell>{c.name}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </ResourceState>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Branches</CardTitle>
        </CardHeader>
        <CardContent>
          <ResourceState resource={branches} emptyText="No branches are visible to your role.">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Code</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((b) => (
                    <TableRow key={b.id}>
                      <TableCell>{b.name}</TableCell>
                      <TableCell>{b.code ?? ""}</TableCell>
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
