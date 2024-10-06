import {
    createProgrammableNft,
    mplTokenMetadata,
} from "@metaplex-foundation/mpl-token-metadata";
import {
    createGenericFile,
    generateSigner,
    percentAmount,
    signerIdentity,
    sol,
} from "@metaplex-foundation/umi";
import { createSignerFromKeypair } from "@metaplex-foundation/umi";
import {
    transferV1,
    createV1,
    TokenStandard,
    mintV1,
    fetchDigitalAsset,
} from "@metaplex-foundation/mpl-token-metadata";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { irysUploader } from "@metaplex-foundation/umi-uploader-irys";
import { base58 } from "@metaplex-foundation/umi/serializers";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import dotenv from "dotenv";

dotenv.config();
const args = process.argv.slice(2);
const imagePath = args[0];
const metadataPath = args[1]; // Now passing metadata file path
const name = args[2];

// Get the current directory name
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const createNft = async (name, ImagePath, MetadataPath) => {
    //
    // ** Setting Up Umi **
    //

    const umi = createUmi("https://api.devnet.solana.com")
        .use(mplTokenMetadata())
        .use(
            irysUploader({
                // mainnet address: "https://node1.irys.xyz"
                // devnet address: "https://devnet.irys.xyz"
                address: "https://devnet.irys.xyz",
            }),
        );

    // You will need to us fs and navigate the filesystem to
    const secretKeyString = process.env.CENTRAL_WALLET_KEY;
    if (!secretKeyString) {
        throw new Error(
            "CENTRAL_WALLET_KEY is not set in environment variables",
        );
    }
    // Parse the stringified array to get the array of numbers (the secret key)
    const secretKey = JSON.parse(secretKeyString);
    let keypair = umi.eddsa.createKeypairFromSecretKey(
        new Uint8Array(secretKey),
    );
    const signer = createSignerFromKeypair(umi, keypair);
    umi.use(signerIdentity(signer));

    //
    // ** Upload an image to Arweave **
    //

    // use `fs` to read file via a string path.
    // You will need to understand the concept of pathing from a computing perspective.

    const imageFile = fs.readFileSync(path.join(ImagePath));

    // Use `createGenericFile` to transform the file into a `GenericFile` type
    // that umi can understand. Make sure you set the mimi tag type correctly
    // otherwise Arweave will not know how to display your image.

    const umiImageFile = createGenericFile(imageFile, `${name}.png`, {
        tags: [{ name: "Content-Type", value: "image/png" }],
    });

    // Here we upload the image to Arweave via Irys and we get returned a uri
    // address where the file is located. You can log this out but as the
    // uploader can takes an array of files it also returns an array of uris.
    // To get the uri we want we can call index [0] in the array.

    const imageUrl = await umi.uploader.upload([umiImageFile]).catch((err) => {
        throw new Error(err);
    });

    const imageUri = imageUrl[0].replace(/arweave\.net/g, "devnet.irys.xyz");

    //
    // ** Upload Metadata to Arweave **
    //
    const metadataJson = fs.readFileSync(path.join(MetadataPath));
    const metadata = JSON.parse(metadataJson);

    // Replace the image URI in the metadata with the uploaded image URI
    metadata.image = imageUri; // Update image URI
    metadata.properties.files[0].uri = imageUri;

    // Call upon umi's uploadJson function to upload our metadata to Arweave via Irys.
    const metadataUrl = await umi.uploader.uploadJson(metadata).catch((err) => {
        throw new Error(err);
    });
    const metadataUri = metadataUrl.replace(/arweave\.net/g, "devnet.irys.xyz");

    //
    // ** Creating the Nft **
    //

    const mint = generateSigner(umi);

    await createV1(umi, {
        mint: mint,
        authority: signer,
        name: name,
        uri: metadataUri,
        sellerFeeBasisPoints: percentAmount(1.0),
        tokenStandard: TokenStandard.NonFungible,
    }).sendAndConfirm(umi);
    await mintV1(umi, {
        mint: mint.publicKey,
        authority: signer,
        amount: 1,
        tokenOwner: signer,
        signer,
        tokenStandard: TokenStandard.NonFungible,
    }).sendAndConfirm(umi);

    const asset = await fetchDigitalAsset(umi, mint.publicKey);
    console.log(
        JSON.stringify({
            mintAddress: mint.publicKey,
        }),
    );
};

// Get command-line arguments
createNft(name, imagePath, metadataPath)
    .then((nftSigner) => {})
    .catch((error) => {
        console.error(error);
    });
