import {compileFromFile} from '../apps/web/node_modules/json-schema-to-typescript/dist/src/index.js';
import {writeFileSync} from 'node:fs';
writeFileSync('packages/contracts/types.ts',await compileFromFile('packages/contracts/schema.json',{bannerComment:'/* Generated from Pydantic. Run scripts/contracts.py and scripts/contracts.mjs. */'}));
