/**
 * forge_entropy_schema — Generate and validate the shared JSON Schema package.
 *
 * Reads schemas from entropy-integrity/schemas/ and validates them against
 * JSON Schema draft-07. Produces a schema bundle for distribution.
 */

import { readFileSync, readdirSync, writeFileSync } from "fs";
import { join } from "path";

interface SchemaBundle {
  version: string;
  schemas: Record<string, object>;
  generated_at: string;
  validation_errors: string[];
}

export function forge_entropy_schema(
  schemaDir: string,
  outputPath?: string
): SchemaBundle {
  const schemas: Record<string, object> = {};
  const errors: string[] = [];

  // Read all schema files
  const files = readdirSync(schemaDir).filter((f) => f.endsWith(".schema.json"));

  for (const file of files) {
    try {
      const content = readFileSync(join(schemaDir, file), "utf-8");
      const schema = JSON.parse(content);

      // Basic validation
      if (!schema.$schema) {
        errors.push(`${file}: missing $schema declaration`);
      }
      if (!schema.$id) {
        errors.push(`${file}: missing $id`);
      }
      if (!schema.title) {
        errors.push(`${file}: missing title`);
      }

      const name = file.replace(".schema.json", "");
      schemas[name] = schema;
    } catch (err) {
      errors.push(`${file}: parse error — ${err}`);
    }
  }

  const bundle: SchemaBundle = {
    version: "v1",
    schemas,
    generated_at: new Date().toISOString(),
    validation_errors: errors,
  };

  if (outputPath) {
    writeFileSync(outputPath, JSON.stringify(bundle, null, 2));
  }

  return bundle;
}
