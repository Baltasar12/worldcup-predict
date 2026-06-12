This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Backend Architecture: Monte Carlo World Cup Simulation

The Python FastAPI backend includes a Monte Carlo simulation engine capable of running thousands of full World Cup realizations. It leverages an Elo-rating based predictive model to estimate win/draw probabilities. The knockout brackets are automatically progressed by resolving matches through the engine (including 50/50 penalty shootouts for draws).

### Performance

The Monte Carlo engine is heavily optimized by loading the dataset and Elo database into memory prior to execution.
- **100 simulations**: ~0.06 seconds
- **500 simulations**: ~0.35 seconds
- **1000 simulations**: ~0.63 seconds
- **5000 simulations**: ~3.15 seconds

### API Endpoints

#### `POST /world-cup/forecast`
Runs a full Monte Carlo simulation to forecast tournament progression probabilities.

**Request:**
```json
{
  "simulations": 5000,
  "seed": 42
}
```
*Note: `seed` is optional. If provided, the simulation is deterministic.*

**Response:**
```json
{
  "simulations": 5000,
  "results": [
    {
      "team": "Argentina",
      "qualified_from_groups": 99.4,
      "round_of_16": 91.2,
      "quarterfinal": 74.5,
      "semifinal": 51.1,
      "final": 31.2,
      "champion": 17.4
    }
  ]
}
```
Results are sorted descending by the `champion` probability.
