import {
  updateV1,
  fetchMetadataFromSeeds,
} from "@metaplex-foundation/mpl-token-metadata";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { createSignerFromKeypair } from "@metaplex-foundation/umi";
import { irysUploader } from "@metaplex-foundation/umi-uploader-irys";
import dotenv from "dotenv";
import fs from "fs";
import {
  createProgrammableNft,
  mplTokenMetadata,
} from "@metaplex-foundation/mpl-token-metadata";
dotenv.config();
import {
  createGenericFile,
  generateSigner,
  percentAmount,
  signerIdentity,
  sol,
} from "@metaplex-foundation/umi";
// Initialize Umi and connect to devnet
const umi = createUmi("https://api.devnet.solana.com")
  .use(mplTokenMetadata())
  .use(
    irysUploader({
      address: "https://devnet.irys.xyz",
    })
  );

// Load keypair from environment variables
const secretKeyString = process.env.CENTRAL_WALLET_KEY;
if (!secretKeyString) {
  throw new Error("CENTRAL_WALLET_KEY is not set in environment variables");
}
const secretKey = JSON.parse(secretKeyString);
let keypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array(secretKey));
const signer = createSignerFromKeypair(umi, keypair);
umi.use(signerIdentity(signer));

const FetchNFT = async (mintAddress) => {
  // Fetch existing metadata using the mint address
  const initialMetadata = await fetchMetadataFromSeeds(umi, {
    mint: mintAddress,
  });
  console.log(
    JSON.stringify({
      uri: initialMetadata.uri,
    })
  );
};

const args = process.argv.slice(2);
const mintAddress = args[0];

FetchNFT(mintAddress).catch((err) => console.error("Error updating NFT:", err));
