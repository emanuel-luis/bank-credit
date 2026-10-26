/** Fields the legacy pages read from the API; phase 4 replaces them with the real contract. */
export interface ApiApplication {
  id: number;
  status: string;
  amount: number;
  term?: string | number;
  title?: string;
  department?: string;
  created_at?: string;
  updated_at?: string;
  deliver_date?: string;
  checklist?: { name?: string; status?: string }[];
  client: {
    nome_fantasia: string;
    razao_social: string;
    cnpj?: string;
    user?: { full_name?: string; email?: string; phone?: string };
  };
}

export interface StoredDocument {
  name: string;
  size?: number;
  type?: string;
}

/** Form values kept in the browser (localStorage) because the API does not store them. */
export interface StoredForm {
  companyName?: string;
  cnpj?: string;
  contactName?: string;
  contactEmail?: string;
  contactPhone?: string;
  documents?: StoredDocument[];
  departamento?: string;
  central?: string;
  purpose?: string;
  status?: string;
  stage?: string;
  term?: string | number;
}

export type Application = ApiApplication & StoredForm;
