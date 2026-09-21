/* Generated from Pydantic. Run scripts/contracts.py and scripts/contracts.mjs. */

export type Id = string;
export type Name = string;
export type SchemaVersion = "1.0";
export type Revision = number;
export type CreatedAt = string;
export type UpdatedAt = string;
export type Synthetic = boolean;
export type PolicyVersion = string;
export type PolicyIds = string[] | null;
export type TemplateVersion = string;
export type Id1 = string;
export type Name1 = string;
export type Scope = "internal" | "external" | "unknown";
export type Systems = System[];
export type Id2 = string;
export type Name2 = string;
export type Zones = Zone[];
export type Id3 = string;
export type Name3 = string;
export type Role = string;
export type SystemId = string | null;
export type Status = "existing" | "new" | "proposed";
export type AssetId = string;
export type Scope1 = "internal" | "external" | "unknown";
export type FormFactor = "unknown" | "physical" | "virtual" | "managed";
export type AuditDestination = string | null;
export type StorageDestination = string | null;
export type LocalOnly = boolean | null;
export type InternetHosted = boolean | null;
export type Evidence = string[];
/**
 * @maxItems 50
 */
export type Components = Component[];
export type Id4 = string;
export type ComponentId = string;
export type ZoneId = string | null;
export type Host = string | null;
export type Site = string | null;
export type Quantity = number | null;
export type RedundancyMode = "unknown" | "active_passive" | "active_active";
export type HostComponentId = string | null;
export type Deployments = Deployment[];
export type Id5 = string;
export type Source = string;
export type Target = string;
export type Purpose = string | null;
export type DataDirection = "source_to_target" | "target_to_source" | "bidirectional" | "unknown";
export type Initiator = string | null;
export type Protocol = string | null;
export type Port = number | null;
export type Enforcement = string[];
export type Delivery = string | null;
export type Evidence1 = string[];
/**
 * @maxItems 100
 */
export type Interfaces = Interface[];
export type Id6 = string;
export type Name4 = string;
export type Version = string;
export type Kind = "document" | "prompt" | "template" | "assistant_proposal";
export type Origin = "prompt" | "upload" | "bundled_demo" | "unknown";
export type Sha256 = string;
export type CanonicalId = string;
export type Variants = string[];
export type Locator = string;
export type Heading = string;
export type Text = string;
export type Page = number | null;
export type Passages = Passage[];
export type Processed = string[];
export type Unprocessed = string[];
export type UnsupportedPages = number[];
export type Sources = Source1[];
export type Id7 = string;
export type SourceId = string;
export type SourceVersion = string;
export type Locator1 = string;
export type Excerpt = string;
export type TargetId = string;
export type Field = string;
export type SourceKind = "document" | "prompt" | "template" | "assistant_proposal";
export type Review = "unreviewed" | "confirmed" | "rejected" | "unknown" | "conflicting";
export type Claims = Claim[];
export type Id8 = string;
export type Scope2 = string;
export type Key = string;
export type Evidence2 = string[];
export type Constraints = Constraint[];
export type Id9 = string;
export type Question = string;
export type TargetId1 = string | null;
export type Field1 = string;
export type Options = string[];
export type Answer = string | null;
export type State = "unknown" | "answered";
export type Evidence3 = string[];
export type Decisions = Decision[];
export type Type = "logical" | "sv1" | "sv2";
export type Revision1 = number;
export type X = number;
export type Y = number;
export type Width = number;
export type Height = number;
export type Visible = boolean;
export type Locked = boolean;
export type Label = string | null;
export type FillColor = string | null;
export type TextColor = string | null;
export type BorderColor = string | null;
export type IconColor = string | null;
export type ZIndex = number;
export type Style = "straight" | "orthogonal";
export type X1 = number;
export type Y1 = number;
/**
 * @maxItems 30
 */
export type Points = Point[];
export type SourceHandle = "left" | "right" | "top" | "bottom";
export type TargetHandle = "left" | "right" | "top" | "bottom";
export type Locked1 = boolean;
export type Automatic = boolean;
export type LineColor = string | null;
export type TextColor1 = string | null;
export type ZIndex1 = number;
export type Notes = string;
export type Id10 = string;
export type ProjectId = string;
export type RequestId = string;
export type BaseRevision = number;
export type Op = "add" | "update" | "remove" | "placement" | "route" | "notes" | "policy_selection" | "project_name";
export type Entity =
  | (
      | "systems"
      | "zones"
      | "components"
      | "deployments"
      | "interfaces"
      | "sources"
      | "claims"
      | "constraints"
      | "decisions"
    )
  | null;
export type Id11 = string;
export type View1 = "logical" | "sv1" | "sv2";
export type Confirmed = boolean;
/**
 * @minItems 1
 * @maxItems 500
 */
export type Operations = Operation[];
export type AffectedIds = string[];
export type Evidence4 = string[];
export type Findings = string[];
export type State1 = "pending" | "accepted" | "rejected";
export type Origin1 = "manual" | "assistant" | "ingest";

export interface Contract {
  project: Project;
  change: ChangeSet;
  [k: string]: unknown;
}
export interface Project {
  id: Id;
  name: Name;
  schema_version: SchemaVersion;
  revision: Revision;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  synthetic: Synthetic;
  policy_version: PolicyVersion;
  policy_ids: PolicyIds;
  template_version: TemplateVersion;
  systems: Systems;
  zones: Zones;
  components: Components;
  deployments: Deployments;
  interfaces: Interfaces;
  sources: Sources;
  claims: Claims;
  constraints: Constraints;
  decisions: Decisions;
  views: Views;
  notes: Notes;
}
export interface System {
  id: Id1;
  name: Name1;
  scope: Scope;
}
export interface Zone {
  id: Id2;
  name: Name2;
}
export interface Component {
  id: Id3;
  name: Name3;
  role: Role;
  system_id: SystemId;
  status: Status;
  asset_id: AssetId;
  scope: Scope1;
  form_factor: FormFactor;
  audit_destination: AuditDestination;
  storage_destination: StorageDestination;
  local_only: LocalOnly;
  internet_hosted: InternetHosted;
  evidence: Evidence;
}
export interface Deployment {
  id: Id4;
  component_id: ComponentId;
  zone_id: ZoneId;
  host: Host;
  site: Site;
  quantity: Quantity;
  redundancy_mode: RedundancyMode;
  host_component_id: HostComponentId;
}
export interface Interface {
  id: Id5;
  source: Source;
  target: Target;
  purpose: Purpose;
  data_direction: DataDirection;
  initiator: Initiator;
  protocol: Protocol;
  port: Port;
  enforcement: Enforcement;
  delivery: Delivery;
  evidence: Evidence1;
}
export interface Source1 {
  id: Id6;
  name: Name4;
  version: Version;
  kind: Kind;
  origin: Origin;
  sha256: Sha256;
  canonical_id: CanonicalId;
  variants: Variants;
  passages: Passages;
  processed: Processed;
  unprocessed: Unprocessed;
  unsupported_pages: UnsupportedPages;
}
export interface Passage {
  locator: Locator;
  heading: Heading;
  text: Text;
  page: Page;
}
export interface Claim {
  id: Id7;
  source_id: SourceId;
  source_version: SourceVersion;
  locator: Locator1;
  excerpt: Excerpt;
  target_id: TargetId;
  field: Field;
  value: Value;
  source_kind: SourceKind;
  review: Review;
}
export interface Value {
  [k: string]: unknown;
}
export interface Constraint {
  id: Id8;
  scope: Scope2;
  key: Key;
  value: Value1;
  evidence: Evidence2;
}
export interface Value1 {
  [k: string]: unknown;
}
export interface Decision {
  id: Id9;
  question: Question;
  target_id: TargetId1;
  field: Field1;
  options: Options;
  answer: Answer;
  state: State;
  evidence: Evidence3;
}
export interface Views {
  [k: string]: View;
}
export interface View {
  type: Type;
  revision: Revision1;
  placements: Placements;
  routes: Routes;
  mappings: Mappings;
}
export interface Placements {
  [k: string]: Placement;
}
export interface Placement {
  x: X;
  y: Y;
  width: Width;
  height: Height;
  visible: Visible;
  locked: Locked;
  label: Label;
  fill_color: FillColor;
  text_color: TextColor;
  border_color: BorderColor;
  icon_color: IconColor;
  z_index: ZIndex;
}
export interface Routes {
  [k: string]: Route;
}
export interface Route {
  style: Style;
  points: Points;
  source_handle: SourceHandle;
  target_handle: TargetHandle;
  locked: Locked1;
  automatic: Automatic;
  label_offset: Point | null;
  line_color: LineColor;
  text_color: TextColor1;
  z_index: ZIndex1;
}
export interface Point {
  x: X1;
  y: Y1;
}
export interface Mappings {
  [k: string]: string[];
}
export interface ChangeSet {
  id?: Id10;
  project_id: ProjectId;
  request_id?: RequestId;
  base_revision: BaseRevision;
  base_views: BaseViews;
  operations: Operations;
  affected_ids?: AffectedIds;
  evidence?: Evidence4;
  findings?: Findings;
  state?: State1;
  origin?: Origin1;
}
export interface BaseViews {
  [k: string]: number;
}
export interface Operation {
  op: Op;
  entity?: Entity;
  id?: Id11;
  value?: Value2;
  view?: View1;
  confirmed?: Confirmed;
}
export interface Value2 {
  [k: string]: unknown;
}
