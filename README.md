# Interactive Demo Tutorial - Satyamev AI Misinformation Verifier

A standalone WhatsApp-style chat demo application for the Satyamev hackathon project (AI for Bharat Hackathon). This application provides judges and users with an interactive chat interface to test AI-powered misinformation verification capabilities for both text claims and images.

## Features

- 🎨 WhatsApp-style chat interface
- 📝 Text claim verification
- 🖼️ Image upload and verification with OCR
- ⚡ Quick demo buttons for instant testing
- 🔄 Fallback mode with mock data for offline demonstrations
- 📱 Mobile-responsive design
- ✨ Smooth animations and transitions
- 🧪 Comprehensive testing with Vitest and fast-check

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5.x
- **Styling**: TailwindCSS 3.x
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library + fast-check
- **Deployment**: AWS S3 + CloudFront or Vercel

## Prerequisites

- Node.js 18+ and npm
- Modern web browser (Chrome 90+, Safari 14+, Firefox 88+)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd frontend-demo
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
   - Copy `.env.development` for local development
   - Update `.env.production` with your API Gateway URL for production

## Development

Start the development server:
```bash
npm run dev
```

The application will open at `http://localhost:5173` with hot module replacement enabled.

## Available Scripts

- `npm run dev` - Start development server on port 5173
- `npm run build` - Build for production (TypeScript compilation + Vite build)
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run test` - Run tests once
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run type-check` - Run TypeScript type checking

## Testing

The project uses a dual testing approach:

### Unit Tests
```bash
npm run test
```

### Property-Based Tests
Property tests use fast-check to verify universal correctness properties across randomized inputs (minimum 100 iterations per test).

### Coverage Report
```bash
npm run test:coverage
```

Coverage targets:
- Overall: 80%
- Components: 85%
- Services: 90%

## Project Structure

```
frontend-demo/
├── src/
│   ├── components/       # React components
│   ├── services/         # API and fallback services
│   ├── types/           # TypeScript type definitions
│   ├── test/            # Test setup and utilities
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles with Tailwind
├── public/              # Static assets
├── .env.development     # Development environment variables
├── .env.production      # Production environment variables
├── vite.config.ts       # Vite configuration
├── vitest.config.ts     # Vitest configuration
├── tailwind.config.js   # TailwindCSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Project dependencies
```

## Environment Variables

### Development (.env.development)
```
VITE_API_BASE_URL=http://localhost:3000
VITE_ENABLE_FALLBACK=true
VITE_API_TIMEOUT=5000
```

### Production (.env.production)
```
VITE_API_BASE_URL=https://your-api-gateway-url.amazonaws.com/prod
VITE_ENABLE_FALLBACK=true
VITE_API_TIMEOUT=5000
```

## Building for Production

1. Update `.env.production` with your API Gateway URL
2. Build the application:
```bash
npm run build
```

The optimized production build will be in the `dist/` directory.

## Deployment

### AWS S3 + CloudFront

See deployment documentation in the project wiki for detailed instructions on:
- S3 bucket configuration
- CloudFront distribution setup
- CORS configuration

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`

## API Integration

The application integrates with existing backend APIs:
- `POST /v1/verify` - Text claim verification
- `POST /v1/verify-image` - Image verification with OCR

### Fallback Mode

When the API is unavailable, the application automatically switches to fallback mode with mock data, allowing demonstrations to continue offline.

## Performance

- Initial render: <1 second
- Bundle size: <500KB
- End-to-end verification: <5 seconds
- UI interactions: <100ms response time

## Browser Support

- Chrome 90+
- Safari 14+
- Firefox 88+
- iOS Safari 14+
- Android Chrome 90+

## Contributing

This is a hackathon demo project. For questions or issues, please contact the development team.

## License

Private - AI for Bharat Hackathon Project
