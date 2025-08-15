"use client";

import React, { useRef, useEffect, useState, useMemo } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Download,
  Maximize2,
  RotateCw,
  Layers,
  Grid3x3,
  Eye,
  Crosshair,
} from "lucide-react";

interface OptimizationResult {
  parameters: Record<string, number>;
  metric: number;
}

interface ParameterSurface3DProps {
  results: OptimizationResult[];
  metricName?: string;
  onPointSelect?: (result: OptimizationResult) => void;
}

export function ParameterSurface3D({
  results,
  metricName = "Sharpe Ratio",
  onPointSelect,
}: ParameterSurface3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);

  const [xParam, setXParam] = useState<string>("");
  const [yParam, setYParam] = useState<string>("");
  const [colorScheme, setColorScheme] = useState<
    "viridis" | "plasma" | "coolwarm"
  >("coolwarm");
  const [showGrid, setShowGrid] = useState(true);
  const [showContours, setShowContours] = useState(false);
  const [crossSectionZ, setCrossSectionZ] = useState(0.5);
  const [viewMode, setViewMode] = useState<"surface" | "heatmap" | "contour">(
    "surface"
  );

  const parameters = useMemo(() => {
    if (results.length === 0) return [];
    return Object.keys(results[0].parameters);
  }, [results]);

  useEffect(() => {
    if (parameters.length >= 2) {
      setXParam(parameters[0]);
      setYParam(parameters[1]);
    }
  }, [parameters]);

  useEffect(() => {
    if (!mountRef.current || !xParam || !yParam) return;

    // Initialize Three.js scene
    const width = mountRef.current.clientWidth;
    const height = 500;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controlsRef.current = controls;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Create surface mesh
    createSurfaceMesh();

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!mountRef.current) return;
      const width = mountRef.current.clientWidth;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [xParam, yParam, results, colorScheme, showGrid, showContours]);

  const createSurfaceMesh = () => {
    if (!sceneRef.current || !xParam || !yParam) return;

    // Remove existing mesh
    if (meshRef.current) {
      sceneRef.current.remove(meshRef.current);
    }

    // Get parameter ranges
    const xValues = results.map((r) => r.parameters[xParam]);
    const yValues = results.map((r) => r.parameters[yParam]);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);

    // Create grid
    const gridSize = 50;
    const geometry = new THREE.PlaneGeometry(4, 4, gridSize - 1, gridSize - 1);

    // Interpolate surface
    const positions = geometry.attributes.position;
    const colors = new Float32Array(positions.count * 3);

    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);

      // Map to parameter space
      const paramX = xMin + ((x + 2) / 4) * (xMax - xMin);
      const paramY = yMin + ((y + 2) / 4) * (yMax - yMin);

      // Find nearest neighbors and interpolate
      const z = interpolateValue(paramX, paramY, xParam, yParam, results);
      positions.setZ(i, z * 2); // Scale for visualization

      // Set color based on value
      const color = getColorForValue(z, colorScheme);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();

    // Create material
    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      shininess: 100,
      specular: 0x222222,
    });

    // Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshRef.current = mesh;
    sceneRef.current.add(mesh);

    // Add grid
    if (showGrid) {
      const gridHelper = new THREE.GridHelper(4, 20, 0x888888, 0xcccccc);
      gridHelper.position.y = -1;
      sceneRef.current.add(gridHelper);
    }

    // Add axes
    const axesHelper = new THREE.AxesHelper(2.5);
    sceneRef.current.add(axesHelper);

    // Add contour lines
    if (showContours) {
      addContourLines(geometry, results);
    }
  };

  const interpolateValue = (
    x: number,
    y: number,
    xParam: string,
    yParam: string,
    results: OptimizationResult[]
  ): number => {
    // Simple inverse distance weighted interpolation
    let weightedSum = 0;
    let totalWeight = 0;

    results.forEach((result) => {
      const dx = result.parameters[xParam] - x;
      const dy = result.parameters[yParam] - y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 0.0001) {
        return result.metric;
      }

      const weight = 1 / (distance * distance);
      weightedSum += result.metric * weight;
      totalWeight += weight;
    });

    return totalWeight > 0 ? weightedSum / totalWeight : 0;
  };

  const getColorForValue = (value: number, scheme: string): THREE.Color => {
    const normalized = Math.max(0, Math.min(1, value));

    switch (scheme) {
      case "coolwarm":
        // Blue to red
        return new THREE.Color(
          normalized,
          0.5 * (1 - Math.abs(normalized - 0.5) * 2),
          1 - normalized
        );
      case "viridis":
        // Purple to yellow-green
        return new THREE.Color(
          0.267 + 0.73 * normalized,
          0.0 + 0.9 * normalized,
          0.329 + 0.126 * normalized
        );
      case "plasma":
        // Purple to pink to yellow
        return new THREE.Color(
          0.05 + 0.95 * normalized,
          0.0 + 0.5 * normalized * normalized,
          0.53 - 0.53 * normalized
        );
      default:
        return new THREE.Color(normalized, normalized, normalized);
    }
  };

  const addContourLines = (
    geometry: THREE.BufferGeometry,
    results: OptimizationResult[]
  ) => {
    // Implementation for contour lines
    // This would analyze the surface and add line segments at specific height intervals
  };

  const handleExport = () => {
    if (!rendererRef.current) return;

    rendererRef.current.render(sceneRef.current!, cameraRef.current!);
    const dataURL = rendererRef.current.domElement.toDataURL("image/png");

    const link = document.createElement("a");
    link.download = `parameter-surface-${Date.now()}.png`;
    link.href = dataURL;
    link.click();
  };

  const resetView = () => {
    if (!cameraRef.current || !controlsRef.current) return;

    cameraRef.current.position.set(5, 5, 5);
    cameraRef.current.lookAt(0, 0, 0);
    controlsRef.current.update();
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>3D Parameter Surface</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{metricName}</Badge>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={resetView}>
                <RotateCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium">X-Axis Parameter</label>
                <Select value={xParam} onValueChange={setXParam}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {parameters.map((param) => (
                      <SelectItem key={param} value={param}>
                        {param}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium">Y-Axis Parameter</label>
                <Select value={yParam} onValueChange={setYParam}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {parameters.map((param) => (
                      <SelectItem key={param} value={param}>
                        {param}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium">Color Scheme</label>
                <Select
                  value={colorScheme}
                  onValueChange={(v) => setColorScheme(v as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="coolwarm">Cool-Warm</SelectItem>
                    <SelectItem value="viridis">Viridis</SelectItem>
                    <SelectItem value="plasma">Plasma</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div
              ref={mountRef}
              className="w-full h-[500px] bg-gray-100 rounded"
            />

            <Tabs defaultValue="controls">
              <TabsList>
                <TabsTrigger value="controls">View Controls</TabsTrigger>
                <TabsTrigger value="crosssection">Cross Sections</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
              </TabsList>

              <TabsContent value="controls" className="space-y-4">
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={showGrid}
                      onChange={(e) => setShowGrid(e.target.checked)}
                    />
                    <Grid3x3 className="h-4 w-4" />
                    Show Grid
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={showContours}
                      onChange={(e) => setShowContours(e.target.checked)}
                    />
                    <Layers className="h-4 w-4" />
                    Show Contours
                  </label>
                </div>
              </TabsContent>

              <TabsContent value="crosssection" className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Z-Plane Cross Section
                  </label>
                  <Slider
                    value={[crossSectionZ]}
                    onValueChange={([value]) => setCrossSectionZ(value)}
                    min={0}
                    max={1}
                    step={0.01}
                  />
                  <p className="text-xs text-muted-foreground">
                    Slice at {(crossSectionZ * 100).toFixed(0)}% of max height
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="analysis" className="space-y-4">
                <ParameterSensitivityAnalysis
                  results={results}
                  xParam={xParam}
                  yParam={yParam}
                />
              </TabsContent>
            </Tabs>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ParameterSensitivityAnalysis({
  results,
  xParam,
  yParam,
}: {
  results: OptimizationResult[];
  xParam: string;
  yParam: string;
}) {
  const analysis = useMemo(() => {
    if (!xParam || !yParam || results.length === 0) return null;

    // Calculate parameter sensitivities
    const xSensitivity = calculateSensitivity(results, xParam);
    const ySensitivity = calculateSensitivity(results, yParam);
    const interaction = calculateInteraction(results, xParam, yParam);

    // Find optimal region
    const optimalRegion = findOptimalRegion(results, xParam, yParam);

    return {
      xSensitivity,
      ySensitivity,
      interaction,
      optimalRegion,
    };
  }, [results, xParam, yParam]);

  if (!analysis) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <p className="text-sm font-medium">{xParam} Sensitivity</p>
              <p className="text-2xl font-bold">
                {analysis.xSensitivity.toFixed(3)}
              </p>
              <p className="text-xs text-muted-foreground">
                Change in metric per unit change
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-1">
              <p className="text-sm font-medium">{yParam} Sensitivity</p>
              <p className="text-2xl font-bold">
                {analysis.ySensitivity.toFixed(3)}
              </p>
              <p className="text-xs text-muted-foreground">
                Change in metric per unit change
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-4">
          <div className="space-y-1">
            <p className="text-sm font-medium">
              Parameter Interaction Strength
            </p>
            <p className="text-2xl font-bold">
              {(analysis.interaction * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground">
              {analysis.interaction > 0.3
                ? "Strong interaction detected"
                : "Weak interaction"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="space-y-1">
            <p className="text-sm font-medium">Optimal Region</p>
            <div className="text-sm space-y-1">
              <p>
                {xParam}: {analysis.optimalRegion.xRange[0].toFixed(2)} -{" "}
                {analysis.optimalRegion.xRange[1].toFixed(2)}
              </p>
              <p>
                {yParam}: {analysis.optimalRegion.yRange[0].toFixed(2)} -{" "}
                {analysis.optimalRegion.yRange[1].toFixed(2)}
              </p>
              <p className="text-muted-foreground">
                Contains top {analysis.optimalRegion.percentage}% of results
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function calculateSensitivity(
  results: OptimizationResult[],
  param: string
): number {
  // Simple numerical derivative calculation
  const values = results.map((r) => ({ x: r.parameters[param], y: r.metric }));
  values.sort((a, b) => a.x - b.x);

  let totalDerivative = 0;
  let count = 0;

  for (let i = 1; i < values.length; i++) {
    const dx = values[i].x - values[i - 1].x;
    const dy = values[i].y - values[i - 1].y;
    if (dx > 0) {
      totalDerivative += Math.abs(dy / dx);
      count++;
    }
  }

  return count > 0 ? totalDerivative / count : 0;
}

function calculateInteraction(
  results: OptimizationResult[],
  param1: string,
  param2: string
): number {
  // Calculate interaction strength using partial derivatives
  // This is a simplified approach
  const correlation = calculateCorrelation(
    results.map((r) => r.parameters[param1]),
    results.map((r) => r.parameters[param2])
  );

  return Math.abs(correlation);
}

function calculateCorrelation(x: number[], y: number[]): number {
  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);
  const sumY2 = y.reduce((sum, yi) => sum + yi * yi, 0);

  const num = n * sumXY - sumX * sumY;
  const den = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

  return den === 0 ? 0 : num / den;
}

function findOptimalRegion(
  results: OptimizationResult[],
  xParam: string,
  yParam: string
): any {
  // Find the region containing top 10% of results
  const sorted = [...results].sort((a, b) => b.metric - a.metric);
  const topCount = Math.ceil(results.length * 0.1);
  const topResults = sorted.slice(0, topCount);

  const xValues = topResults.map((r) => r.parameters[xParam]);
  const yValues = topResults.map((r) => r.parameters[yParam]);

  return {
    xRange: [Math.min(...xValues), Math.max(...xValues)],
    yRange: [Math.min(...yValues), Math.max(...yValues)],
    percentage: 10,
  };
}
