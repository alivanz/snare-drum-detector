import { getFormProps, getInputProps, useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";
import { kebabCase } from "change-case";
import {
	Form,
	Link,
	useActionData,
	useLoaderData,
	useNavigation,
} from "react-router";
import { z } from "zod";
import type { Route } from "./+types/locations";

const locationSchema = z.object({
	name: z.string().min(1, "Location name is required"),
});

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Manage Locations - Snare Drum Challenge" },
		{
			name: "description",
			content: "Manage city locations for local leaderboards",
		},
	];
}

export async function loader({ context }: Route.LoaderArgs) {
	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	const locations = await stub.getLocations();

	return {
		locations,
	};
}

export async function action({ request, context }: Route.ActionArgs) {
	const formData = await request.formData();
	const submission = parseWithZod(formData, { schema: locationSchema });

	if (submission.status !== "success") {
		return submission.reply();
	}

	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	const locationId = kebabCase(submission.value.name);
	
	// Check if location already exists
	const existingLocations = await stub.getLocations();
	const locationExists = existingLocations.some(loc => loc.id === locationId);
	
	if (locationExists) {
		return submission.reply({
			formErrors: [`Location "${submission.value.name}" already exists`],
		});
	}

	await stub.addLocation({
		id: locationId,
		name: submission.value.name,
	});

	return submission.reply({ resetForm: true });
}

export default function Locations() {
	const { locations } = useLoaderData<typeof loader>();
	const navigation = useNavigation();
	const lastResult = useActionData<typeof action>();

	const [form, fields] = useForm({
		lastResult,
		onValidate({ formData }) {
			return parseWithZod(formData, { schema: locationSchema });
		},
		shouldValidate: "onBlur",
	});

	const isSubmitting = navigation.state === "submitting";

	return (
		<div
			className="min-h-screen flex flex-col items-center justify-center p-4"
			style={{
				backgroundImage: "url(/background.jpg)",
				backgroundSize: "cover",
				backgroundPosition: "center",
				backgroundRepeat: "no-repeat",
			}}
		>
			<div className="bg-black/60 backdrop-blur-sm rounded-lg p-12 border-2 border-white/30 max-w-4xl w-full">
				<h1 className="text-3xl text-white uppercase tracking-widest mb-8 text-center font-bold">
					MANAGE LOCATIONS
				</h1>

				{/* Add Location Form */}
				<div className="mb-8 p-6 bg-black/40 rounded-lg border border-white/20">
					<h2 className="text-xl text-white uppercase tracking-wider mb-4">
						Add New Location
					</h2>
					<Form method="post" {...getFormProps(form)}>
						{form.errors && (
							<div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded">
								<p className="text-red-400">{form.errors[0]}</p>
							</div>
						)}
						<div className="flex gap-4">
							<div className="flex-1">
								<input
									{...getInputProps(fields.name, { type: "text" })}
									placeholder="Enter city name..."
									className="w-full px-4 py-3 bg-black/50 border border-white/30 text-white rounded focus:outline-none focus:border-white/60 placeholder-white/40"
								/>
								{fields.name.errors && (
									<p className="text-red-400 text-sm mt-2">
										{fields.name.errors[0]}
									</p>
								)}
							</div>
							<button
								type="submit"
								disabled={isSubmitting}
								className="px-8 py-3 rounded-lg font-bold uppercase tracking-wider transition-all"
								style={{
									background:
										"linear-gradient(180deg, #E0E0E0 0%, #9E9E9E 50%, #757575 100%)",
									boxShadow:
										"0 4px 8px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)",
									color: "black",
									cursor: isSubmitting ? "not-allowed" : "pointer",
								}}
							>
								{isSubmitting ? "Adding..." : "Add Location"}
							</button>
						</div>
					</Form>
				</div>

				{/* Locations Table */}
				<div className="overflow-x-auto">
					<table className="w-full text-white">
						<thead>
							<tr className="border-b border-white/30">
								<th className="text-left py-3 px-4 uppercase tracking-wider text-sm text-white/80">
									ID
								</th>
								<th className="text-left py-3 px-4 uppercase tracking-wider text-sm text-white/80">
									Name
								</th>
								<th className="text-right py-3 px-4 uppercase tracking-wider text-sm text-white/80">
									Total Scores
								</th>
							</tr>
						</thead>
						<tbody>
							{locations.length === 0 ? (
								<tr>
									<td colSpan={3} className="text-center py-8 text-white/60">
										No locations added yet
									</td>
								</tr>
							) : (
								locations.map((location) => (
									<tr
										key={location.id}
										className="border-b border-white/10 hover:bg-white/5 transition-colors"
									>
										<td className="py-3 px-4 font-mono text-sm">
											{location.id}
										</td>
										<td className="py-3 px-4">{location.name}</td>
										<td className="py-3 px-4 text-right">0</td>
									</tr>
								))
							)}
						</tbody>
					</table>
				</div>
			</div>

			{/* Back to Home */}
			<div className="mt-8">
				<Link
					to="/"
					className="text-white text-lg uppercase tracking-wider hover:text-white/80 transition-colors underline"
				>
					Back to Home
				</Link>
			</div>
		</div>
	);
}
