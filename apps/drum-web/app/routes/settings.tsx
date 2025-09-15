import { getFormProps, getSelectProps, useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";
import {
	Form,
	Link,
	useActionData,
	useLoaderData,
	useNavigation,
} from "react-router";
import { z } from "zod";
import type { Route } from "./+types/settings";

const settingsSchema = z.object({
	locationId: z.string().min(1, "Please select a city"),
});

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Settings - Snare Drum Challenge" },
		{
			name: "description",
			content: "Select your city to compete on local leaderboards!",
		},
	];
}

export async function loader({ context }: Route.LoaderArgs) {
	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	const locations = await stub.getLocations();
	const currentSettings = await stub.getSettings();

	return {
		locations,
		currentSettings,
	};
}

export async function action({ request, context }: Route.ActionArgs) {
	const formData = await request.formData();
	const submission = parseWithZod(formData, { schema: settingsSchema });

	if (submission.status !== "success") {
		return submission.reply();
	}

	const scoreStorage = context.cloudflare.env.SCORE_STORAGE;
	const id = scoreStorage.idFromName("global");
	const stub = scoreStorage.get(id);

	await stub.updateSettings(submission.value.locationId);

	return submission.reply({ resetForm: true });
}

export default function Settings() {
	const { locations, currentSettings } = useLoaderData<typeof loader>();
	const navigation = useNavigation();
	const lastResult = useActionData<typeof action>();

	const [form, fields] = useForm({
		lastResult,
		defaultValue: {
			locationId: currentSettings?.locationId || "",
		},
		onValidate({ formData }) {
			return parseWithZod(formData, { schema: settingsSchema });
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
			{/* Settings Card */}
			<div className="bg-black/60 backdrop-blur-sm rounded-lg p-12 border-2 border-white/30 min-w-[500px]">
				<h1 className="text-3xl text-white uppercase tracking-widest mb-8 text-center font-bold">
					SETTINGS
				</h1>

				<Form method="post" {...getFormProps(form)}>
					<div className="mb-8">
						<label
							htmlFor={fields.locationId.id}
							className="block text-white/80 uppercase tracking-wider text-sm mb-4"
						>
							SELECT YOUR CITY
						</label>
						<select
							{...getSelectProps(fields.locationId)}
							className="w-full px-4 py-3 bg-black/50 border border-white/30 text-white rounded focus:outline-none focus:border-white/60"
						>
							<option value="">Choose a city...</option>
							{locations.map((city) => (
								<option key={city.id} value={city.id}>
									{city.name}
								</option>
							))}
						</select>
						{fields.locationId.errors && (
							<p className="text-red-400 text-sm mt-2">
								{fields.locationId.errors[0]}
							</p>
						)}
					</div>

					{/* Save Button */}
					<button
						type="submit"
						disabled={isSubmitting}
						className="w-full px-6 py-4 rounded-lg font-bold text-2xl uppercase tracking-wider transition-all"
						style={{
							background:
								"linear-gradient(180deg, #E0E0E0 0%, #9E9E9E 50%, #757575 100%)",
							boxShadow:
								"0 4px 8px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)",
							color: "black",
							cursor: isSubmitting ? "not-allowed" : "pointer",
						}}
					>
						{isSubmitting ? "Saving..." : "Save"}
					</button>
				</Form>
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
