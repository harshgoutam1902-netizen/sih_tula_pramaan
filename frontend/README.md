# TulaPramaan Frontend

React + TypeScript frontend for the 3-Stage Smart Form System.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **API Client**: Axios
- **Validation**: Zod
- **Styling**: Tailwind CSS
- **Testing**: Vitest + Testing Library

## Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Stage1/       # Stage 1 parameter collection
│   ├── Stage1_5/     # Classification confirmation
│   ├── Stage2/       # Test execution dashboard & forms
│   └── Stage3/       # Environment capture
├── lib/
│   └── api/          # API client and endpoints
├── hooks/            # Custom React hooks
├── stores/           # Zustand stores
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── App.tsx           # Main app component
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Environment Variables

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Development Server

```bash
npm run dev
```

Server starts on http://localhost:3000

### Build for Production

```bash
npm run build
```

### Run Tests

```bash
npm test
```

## API Integration

The frontend uses a type-safe API client that matches the backend Pydantic models:

```typescript
import { classificationApi } from '@/lib/api';

// Determine classification
const result = await classificationApi.determine({
  e: '0.001',
  max_capacity: '150',
});

console.log(result.status); // "DETERMINED"
console.log(result.class_); // "II"
```

All API types are defined in `src/types/api.ts` and stay in sync with backend models.

## State Management

Using Zustand for global state:

```typescript
import { useClassificationStore } from '@/stores/classification';

function MyComponent() {
  const { classResult, setClassResult } = useClassificationStore();
  
  // Use classification result
  return <div>{classResult?.class_}</div>;
}
```

## React Query Integration

TanStack Query for server state management:

```typescript
import { useQuery } from '@tanstack/react-query';
import { classificationApi } from '@/lib/api';

function MyComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ['classification-history', instrumentId],
    queryFn: () => classificationApi.getHistory(instrumentId),
  });
  
  if (isLoading) return <div>Loading...</div>;
  return <div>{JSON.stringify(data)}</div>;
}
```

## Component Structure (To Be Implemented)

### Stage 1: Parameter Collection
- `Stage1Form.tsx` - Main form component
- `ClassificationParamsFields.tsx` - e, Max, Min inputs
- `CategoryParamsFields.tsx` - Self-indicating, electronic, etc.
- `MultiRangeFields.tsx` - Sub-range inputs

### Stage 1.5: Classification Confirmation
- `ClassificationResult.tsx` - Result display
- `DeterminedResult.tsx` - Single class match
- `AmbiguousResult.tsx` - Multiple candidates, requires choice
- `InvalidResult.tsx` - No match, error display

### Stage 2: Test Execution
- `TestDashboard.tsx` - Progress and test list
- `TestForm.tsx` - Generic test form template
- `TestFormVariants/` - Specific test forms
  - `DiscriminationTest.tsx`
  - `TiltingTest.tsx`
- `LiveMPEFeedback.tsx` - Real-time pass/fail indicators

### Stage 3: Environment
- `EnvironmentSessionForm.tsx` - Session start conditions
- `EnvironmentReadingFields.tsx` - Temp, humidity, pressure, time
- `EnvironmentOverrideButton.tsx` - Manual override for long tests

## Development Guidelines

### Code Style

- Use TypeScript strict mode
- All API calls typed with Zod schemas
- Component props documented with JSDoc
- Use Decimal.js for precision calculations

### Testing

```bash
# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Type check
npm run type-check
```

### Linting

```bash
npm run lint
```

## Deployment

Build generates static files in `dist/`:

```bash
npm run build
cd dist
# Serve with any static file server
```

Can deploy to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting

## Next Steps

1. Implement Stage 1 form components
2. Integrate with backend classification API
3. Build Stage 1.5 confirmation UI
4. Create test dashboard (Stage 2)
5. Add OCR integration for nameplate/display photos
6. Implement environment capture (Stage 3)
